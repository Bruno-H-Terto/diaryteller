"""Shared quota periods, states and exceptions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from diary_contracts.quota import QuotaPeriod, UploadMetric
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_upload_quota import UploadQuotaBucketTable

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
FAR_FUTURE = datetime(9999, 12, 31, tzinfo=UTC)
DAILY_METRICS = {
    UploadMetric.DAILY_UPLOAD_COUNT.value,
    UploadMetric.DAILY_UPLOAD_BYTES.value,
}


class QuotaExceeded(Exception):
    """The requested units do not fit the current bucket."""

    def __init__(self, metric: str, limit: int, used: int, reserved: int, amount: int) -> None:
        super().__init__(metric)
        self.metric = metric
        self.limit = limit
        self.used = used
        self.reserved = reserved
        self.amount = amount


class ReservationConflict(Exception):
    """A settled reservation cannot be reserved or committed again."""


@dataclass(frozen=True, slots=True)
class QuotaState:
    """Current numbers for one metric and period."""

    metric: str
    used: int
    reserved: int
    limit: int
    reset_at: datetime
    bucket_date: date | None
    reservation_id: uuid.UUID | None = None


def period_for(metric: str, now: datetime) -> tuple[str, date | None, datetime, datetime]:
    """Return kind, bucket date, period start and reset."""
    if metric in DAILY_METRICS:
        start = datetime(now.year, now.month, now.day, tzinfo=UTC)
        return QuotaPeriod.DAILY.value, start.date(), start, start + timedelta(days=1)
    return QuotaPeriod.CAPACITY.value, None, EPOCH, FAR_FUTURE


async def load_bucket(
    session: AsyncSession, owner_id: uuid.UUID, metric: str, period_start: datetime
) -> UploadQuotaBucketTable | None:
    """Load one bucket row."""
    return await session.scalar(
        select(UploadQuotaBucketTable).where(
            UploadQuotaBucketTable.owner_id == owner_id,
            UploadQuotaBucketTable.metric == metric,
            UploadQuotaBucketTable.period_start == period_start,
        )
    )


async def load_state(
    session: AsyncSession,
    owner_id: uuid.UUID,
    metric: str,
    now: datetime,
    reservation_id: uuid.UUID | None = None,
) -> QuotaState:
    """Build the current state for one metric."""
    _, bucket_date, period_start, reset_at = period_for(metric, now)
    row = await load_bucket(session, owner_id, metric, period_start)
    return QuotaState(
        metric=metric,
        used=row.used if row else 0,
        reserved=row.reserved if row else 0,
        limit=row.limit if row else 0,
        reset_at=reset_at,
        bucket_date=bucket_date,
        reservation_id=reservation_id,
    )
