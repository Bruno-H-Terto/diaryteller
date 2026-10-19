"""Small pure helpers shared by the upload quota use cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.quota import QuotaAmount, QuotaErrorDetails, UploadMetric

from identity.adapters.postgres.upload_quota_shared import QuotaExceeded, QuotaState

EXCEEDED_CODES = {
    UploadMetric.DAILY_UPLOAD_COUNT.value: ErrorCode.DAILY_UPLOAD_COUNT_EXCEEDED,
    UploadMetric.DAILY_UPLOAD_BYTES.value: ErrorCode.DAILY_UPLOAD_BYTES_EXCEEDED,
    UploadMetric.RETAINED_STORAGE_BYTES.value: ErrorCode.STORAGE_QUOTA_EXCEEDED,
    UploadMetric.CONCURRENT_UPLOADS.value: ErrorCode.UPLOAD_CONCURRENCY_EXCEEDED,
}


def window_for(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


def amount_of(state: QuotaState, fallback_limit: int) -> QuotaAmount:
    """Use the plan limit until the first bucket row exists."""
    limit = state.limit or fallback_limit
    return QuotaAmount(
        used=state.used,
        reserved=state.reserved,
        limit=limit,
        remaining=max(0, limit - state.used - state.reserved),
    )


def limit_for(plan_limits: dict[str, int], metric: UploadMetric) -> int:
    """Fail closed when a plan omits a metered limit."""
    value = plan_limits.get(metric.value)
    return int(value) if value is not None else 0


def quota_exceeded(exc: QuotaExceeded, now: datetime) -> DomainError:
    """Translate a bucket rejection into the documented mobile error."""
    _, reset_at = window_for(now)
    details = QuotaErrorDetails(
        metric=UploadMetric(exc.metric),
        limit=exc.limit,
        used=exc.used,
        reserved=exc.reserved,
        requested=exc.amount,
        reset_at=reset_at,
    )
    return DomainError(
        EXCEEDED_CODES[exc.metric],
        429,
        "Upload quota exceeded",
        details=details.model_dump(mode="json"),
    )


def reservation_conflict() -> DomainError:
    """A settled reservation cannot be reserved or settled again."""
    return DomainError(ErrorCode.UPLOAD_STATE_INVALID, 409, "Reservation is not settled")
