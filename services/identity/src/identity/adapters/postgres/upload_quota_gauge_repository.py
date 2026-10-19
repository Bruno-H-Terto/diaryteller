"""Idempotent capacity gauges: concurrency, close, expiry and reset."""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.quota import UploadMetric
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_upload_quota import (
    UploadQuotaAdjustmentTable,
    UploadQuotaBucketTable,
    UploadReservationTable,
)
from .upload_quota_shared import QuotaExceeded, QuotaState, load_state, period_for


class PostgresUploadQuotaGaugeRepository:
    """Gauge changes guarded by unique adjustment references."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def acquire(
        self,
        owner_id: uuid.UUID,
        metric: UploadMetric,
        amount: int,
        limit: int,
        reference: str,
        now: datetime,
    ) -> QuotaState:
        """Idempotently increase a capacity gauge (concurrent uploads)."""
        kind, bucket_date, period_start, _ = period_for(metric.value, now)
        async with self._session.begin_nested():
            inserted = await self._session.scalar(
                insert(UploadQuotaAdjustmentTable)
                .values(
                    id=uuid.uuid4(),
                    owner_id=owner_id,
                    metric=metric.value,
                    amount=amount,
                    reason="acquire",
                    reference=reference,
                    created_at=now,
                )
                .on_conflict_do_nothing(constraint="uq_upload_adjustment_ref")
                .returning(UploadQuotaAdjustmentTable.id)
            )
            if inserted is not None:
                updated = await self._session.scalar(
                    insert(UploadQuotaBucketTable)
                    .values(
                        id=uuid.uuid4(),
                        owner_id=owner_id,
                        metric=metric.value,
                        period_kind=kind,
                        bucket_date=bucket_date,
                        period_start=period_start,
                        used=amount,
                        reserved=0,
                        limit=limit,
                    )
                    .on_conflict_do_update(
                        constraint="uq_upload_quota_bucket",
                        set_={"used": UploadQuotaBucketTable.used + amount, "limit": limit},
                        where=UploadQuotaBucketTable.used + amount <= limit,
                    )
                    .returning(UploadQuotaBucketTable.id)
                )
                if updated is None:
                    raise QuotaExceeded(metric.value, limit, 0, 0, amount)
        return await load_state(self._session, owner_id, metric.value, now)

    async def close(
        self,
        owner_id: uuid.UUID,
        metric: UploadMetric,
        amount: int,
        reference: str,
        now: datetime,
    ) -> None:
        """Idempotently decrease a capacity gauge when a resource is destroyed."""
        async with self._session.begin_nested():
            inserted = await self._session.scalar(
                insert(UploadQuotaAdjustmentTable)
                .values(
                    id=uuid.uuid4(),
                    owner_id=owner_id,
                    metric=metric.value,
                    amount=-amount,
                    reason="close",
                    reference=reference,
                    created_at=now,
                )
                .on_conflict_do_nothing(constraint="uq_upload_adjustment_ref")
                .returning(UploadQuotaAdjustmentTable.id)
            )
            if inserted is not None:
                _, _, period_start, _ = period_for(metric.value, now)
                await self._session.execute(
                    update(UploadQuotaBucketTable)
                    .where(
                        UploadQuotaBucketTable.owner_id == owner_id,
                        UploadQuotaBucketTable.metric == metric.value,
                        UploadQuotaBucketTable.period_start == period_start,
                    )
                    .values(used=func.greatest(0, UploadQuotaBucketTable.used - amount))
                )

    async def expire_stale(self, now: datetime) -> int:
        """Release reservations whose TTL elapsed without settlement."""
        rows = list(
            await self._session.scalars(
                select(UploadReservationTable)
                .where(
                    UploadReservationTable.state == "RESERVED",
                    UploadReservationTable.expires_at < now,
                )
                .with_for_update(skip_locked=True)
            )
        )
        for row in rows:
            row.state = "EXPIRED"
            row.settled_at = now
            await self._session.execute(
                update(UploadQuotaBucketTable)
                .where(
                    UploadQuotaBucketTable.owner_id == row.owner_id,
                    UploadQuotaBucketTable.metric == row.metric,
                    UploadQuotaBucketTable.period_start == row.period_start,
                )
                .values(reserved=func.greatest(0, UploadQuotaBucketTable.reserved - row.amount))
            )
        await self._session.flush()
        return len(rows)

    async def reset_owner(self, owner_id: uuid.UUID) -> None:
        """Remove all quota state for an account being deleted."""
        for table in (
            UploadQuotaAdjustmentTable,
            UploadReservationTable,
            UploadQuotaBucketTable,
        ):
            await self._session.execute(delete(table).where(table.owner_id == owner_id))

    async def snapshot(
        self, owner_id: uuid.UUID, metrics: list[UploadMetric], now: datetime
    ) -> dict[str, QuotaState]:
        """Return current numbers for the requested metrics."""
        return {
            metric.value: await load_state(self._session, owner_id, metric.value, now)
            for metric in metrics
        }
