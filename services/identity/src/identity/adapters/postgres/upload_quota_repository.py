"""Atomic upload quota reservations: reserve, commit and release.

Daily metrics reset at UTC midnight. Reservations are settled exactly once, so
retries and concurrent completion cannot double count.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from diary_contracts.quota import UploadMetric
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_upload_quota import UploadQuotaBucketTable, UploadReservationTable
from .upload_quota_shared import (
    QuotaExceeded,
    QuotaState,
    ReservationConflict,
    load_bucket,
    load_state,
    period_for,
)


class PostgresUploadQuotaRepository:
    """Quota reservations bound to a request transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def reserve(
        self,
        owner_id: uuid.UUID,
        metric: UploadMetric,
        amount: int,
        limit: int,
        reference: str,
        ttl_seconds: int,
        now: datetime,
    ) -> QuotaState:
        """Reserve units or return the existing live reservation."""
        kind, bucket_date, period_start, _ = period_for(metric.value, now)
        reservation_id = uuid.uuid4()
        inserted = await self._session.scalar(
            insert(UploadReservationTable)
            .values(
                id=reservation_id,
                owner_id=owner_id,
                metric=metric.value,
                bucket_date=bucket_date,
                period_start=period_start,
                amount=amount,
                state="RESERVED",
                reference=reference,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl_seconds),
            )
            .on_conflict_do_nothing(constraint="uq_upload_reservation_ref")
            .returning(UploadReservationTable.id)
        )
        if inserted is None:
            existing = await self._session.scalar(
                select(UploadReservationTable).where(
                    UploadReservationTable.owner_id == owner_id,
                    UploadReservationTable.metric == metric.value,
                    UploadReservationTable.reference == reference,
                )
            )
            if existing is None or existing.state not in {"RESERVED", "COMMITTED"}:
                raise ReservationConflict(reference)
            return await load_state(self._session, owner_id, metric.value, now, existing.id)
        bucket_id = await self._session.scalar(
            insert(UploadQuotaBucketTable)
            .values(
                id=uuid.uuid4(),
                owner_id=owner_id,
                metric=metric.value,
                period_kind=kind,
                bucket_date=bucket_date,
                period_start=period_start,
                used=0,
                reserved=amount,
                limit=limit,
            )
            .on_conflict_do_update(
                constraint="uq_upload_quota_bucket",
                set_={
                    "reserved": UploadQuotaBucketTable.reserved + amount,
                    "limit": limit,
                },
                where=(
                    UploadQuotaBucketTable.used + UploadQuotaBucketTable.reserved + amount <= limit
                ),
            )
            .returning(UploadQuotaBucketTable.id)
        )
        if bucket_id is None:
            bucket = await load_bucket(self._session, owner_id, metric.value, period_start)
            await self._session.execute(
                update(UploadReservationTable)
                .where(UploadReservationTable.id == reservation_id)
                .values(state="RELEASED", settled_at=now)
            )
            raise QuotaExceeded(
                metric.value,
                limit,
                bucket.used if bucket else 0,
                bucket.reserved if bucket else 0,
                amount,
            )
        return await load_state(self._session, owner_id, metric.value, now, reservation_id)

    async def commit(self, owner_id: uuid.UUID, reservation_id: uuid.UUID, now: datetime) -> None:
        """Move reserved units into definitive consumption exactly once."""
        row = await self._session.scalar(
            select(UploadReservationTable)
            .where(UploadReservationTable.id == reservation_id)
            .with_for_update()
        )
        if row is None or row.owner_id != owner_id:
            raise ReservationConflict(str(reservation_id))
        if row.state == "COMMITTED":
            return
        if row.state != "RESERVED":
            raise ReservationConflict(str(reservation_id))
        row.state = "COMMITTED"
        row.settled_at = now
        await self._session.flush()
        await self._session.execute(
            update(UploadQuotaBucketTable)
            .where(
                UploadQuotaBucketTable.owner_id == owner_id,
                UploadQuotaBucketTable.metric == row.metric,
                UploadQuotaBucketTable.period_start == row.period_start,
            )
            .values(
                used=UploadQuotaBucketTable.used + row.amount,
                reserved=func.greatest(0, UploadQuotaBucketTable.reserved - row.amount),
            )
        )

    async def release(self, owner_id: uuid.UUID, reservation_id: uuid.UUID, now: datetime) -> None:
        """Release unused units; committed consumption is never refunded."""
        row = await self._session.scalar(
            select(UploadReservationTable)
            .where(UploadReservationTable.id == reservation_id)
            .with_for_update()
        )
        if row is None or row.owner_id != owner_id:
            raise ReservationConflict(str(reservation_id))
        if row.state != "RESERVED":
            return
        row.state = "RELEASED"
        row.settled_at = now
        await self._session.flush()
        await self._session.execute(
            update(UploadQuotaBucketTable)
            .where(
                UploadQuotaBucketTable.owner_id == owner_id,
                UploadQuotaBucketTable.metric == row.metric,
                UploadQuotaBucketTable.period_start == row.period_start,
            )
            .values(reserved=func.greatest(0, UploadQuotaBucketTable.reserved - row.amount))
        )
