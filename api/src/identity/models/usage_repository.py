"""Atomic quota buckets and reservations.

The conditional upsert prevents concurrent requests from exceeding a limit.
Finalization replaces the reserved estimate with known consumption or releases
unused units without claiming that a provider stopped billing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.subscription import ReservationState, daily_period_start

from .tables_access import UsageBucketTable, UsageReservationTable


class PostgresUsageRepository:
    """Usage buckets and reservations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def reserve(
        self, user_id: uuid.UUID, metric: str, amount: int, limit: int, period_start: datetime
    ) -> bool:
        """Reserve atomically; false when the quota would be exceeded."""
        if amount < 0 or amount > limit:
            return False
        stmt = insert(UsageBucketTable).values(
            id=uuid.uuid4(),
            user_id=user_id,
            metric=metric,
            period_start=period_start,
            used=amount,
            limit=limit,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_usage_bucket",
            set_={"used": UsageBucketTable.used + amount, "limit": limit},
            where=UsageBucketTable.used + amount <= limit,
        ).returning(UsageBucketTable.id)
        result = await self._session.execute(stmt)
        return result.first() is not None

    async def finalize(
        self,
        user_id: uuid.UUID,
        metric: str,
        reserved: int,
        actual: int,
        period_start: datetime,
    ) -> None:
        """Replace reserved units with actual known consumption."""
        delta = actual - reserved
        await self._session.execute(
            update(UsageBucketTable)
            .where(
                UsageBucketTable.user_id == user_id,
                UsageBucketTable.metric == metric,
                UsageBucketTable.period_start == period_start,
            )
            .values(used=func.greatest(0, UsageBucketTable.used + delta))
        )

    async def release(
        self, user_id: uuid.UUID, metric: str, amount: int, period_start: datetime
    ) -> None:
        """Release units after a failed/abandoned call."""
        await self._session.execute(
            update(UsageBucketTable)
            .where(
                UsageBucketTable.user_id == user_id,
                UsageBucketTable.metric == metric,
                UsageBucketTable.period_start == period_start,
            )
            .values(used=func.greatest(0, UsageBucketTable.used - amount))
        )

    async def snapshot(self, user_id: uuid.UUID, now: datetime) -> dict[str, tuple[int, int]]:
        """Return current used/limit per metric."""
        period_start = daily_period_start(now)
        rows = await self._session.scalars(
            select(UsageBucketTable).where(
                UsageBucketTable.user_id == user_id,
                UsageBucketTable.period_start == period_start,
            )
        )
        return {row.metric: (row.used, row.limit) for row in rows}

    async def create_reservation(
        self,
        operation_id: uuid.UUID,
        user_id: uuid.UUID,
        metric: str,
        amount: int,
        period_start: datetime,
        now: datetime,
    ) -> None:
        """Persist the reservation associated with a receipt."""
        self._session.add(
            UsageReservationTable(
                id=uuid.uuid4(),
                operation_id=operation_id,
                user_id=user_id,
                metric=metric,
                amount=amount,
                state=ReservationState.RESERVED.value,
                period_start=period_start,
                created_at=now,
                expires_at=now + timedelta(hours=24),
            )
        )
        await self._session.flush()

    async def finish_reservation(
        self, operation_id: uuid.UUID, state: ReservationState, now: datetime
    ) -> None:
        """Mark a reservation finished or abandoned."""
        await self._session.execute(
            update(UsageReservationTable)
            .where(UsageReservationTable.operation_id == operation_id)
            .values(state=state.value, finished_at=now)
        )

    async def expired_reservations(self, now: datetime) -> list[UsageReservationTable]:
        """Reservations past their expiry that still need reconciliation."""
        rows = await self._session.scalars(
            select(UsageReservationTable).where(
                UsageReservationTable.state == ReservationState.RESERVED.value,
                UsageReservationTable.expires_at < now,
            )
        )
        return list(rows)
