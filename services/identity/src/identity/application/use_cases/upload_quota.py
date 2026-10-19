"""Upload quota use cases built on the effective plan.

Limits come from the stored plan, never from the request. Daily counters reset
at 00:00 UTC; storage and concurrency are long-lived capacity gauges.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from diary_contracts.quota import QuotaReservationView, UploadMetric, UploadQuota

from identity.adapters.postgres.upload_quota_shared import (
    QuotaExceeded,
    QuotaState,
    ReservationConflict,
)
from identity.application.ports.subscription import PlanRepository, SubscriptionRepository
from identity.application.ports.upload_quota import (
    UploadQuotaGaugeRepository,
    UploadQuotaRepository,
)

from .plan_resolution import resolve_plan
from .upload_quota_rules import (
    amount_of,
    limit_for,
    quota_exceeded,
    reservation_conflict,
    window_for,
)

METERED_METRICS = (
    UploadMetric.DAILY_UPLOAD_COUNT,
    UploadMetric.DAILY_UPLOAD_BYTES,
    UploadMetric.RETAINED_STORAGE_BYTES,
    UploadMetric.CONCURRENT_UPLOADS,
)


async def upload_quota_view(
    *,
    user_id: UUID,
    plan_repo: PlanRepository,
    subscriptions: SubscriptionRepository,
    gauges: UploadQuotaGaugeRepository,
    now: datetime,
) -> UploadQuota:
    """Assemble `/v1/me/upload-quota` from stored counters and plan limits."""
    plan = await resolve_plan(
        user_id=user_id, now=now, plans=plan_repo, subscriptions=subscriptions
    )
    snapshot = await gauges.snapshot(user_id, list(METERED_METRICS), now)
    limits = plan.upload_limits
    window_start, reset_at = window_for(now)
    return UploadQuota(
        tier=plan.code,
        window_start=window_start,
        reset_at=reset_at,
        daily_upload_count=amount_of(
            snapshot[UploadMetric.DAILY_UPLOAD_COUNT.value],
            limit_for(limits, UploadMetric.DAILY_UPLOAD_COUNT),
        ),
        daily_upload_bytes=amount_of(
            snapshot[UploadMetric.DAILY_UPLOAD_BYTES.value],
            limit_for(limits, UploadMetric.DAILY_UPLOAD_BYTES),
        ),
        retained_storage_bytes=amount_of(
            snapshot[UploadMetric.RETAINED_STORAGE_BYTES.value],
            limit_for(limits, UploadMetric.RETAINED_STORAGE_BYTES),
        ),
        max_file_bytes=int(limits["max_file_bytes"]),
        max_context_bytes=int(limits["max_context_bytes"]),
        max_context_records=int(limits["max_context_records"]),
        max_audio_seconds=int(limits["max_audio_seconds"]),
        max_concurrent_uploads=int(limits[UploadMetric.CONCURRENT_UPLOADS.value]),
    )


async def reserve_upload(
    *,
    user_id: UUID,
    metric: UploadMetric,
    amount: int,
    reference: str,
    ttl_seconds: int,
    plan_repo: PlanRepository,
    subscriptions: SubscriptionRepository,
    reservations: UploadQuotaRepository,
    now: datetime,
) -> QuotaReservationView:
    """Reserve metered units before signing or accepting content."""
    plan = await resolve_plan(
        user_id=user_id, now=now, plans=plan_repo, subscriptions=subscriptions
    )
    limit = limit_for(plan.upload_limits, metric)
    try:
        state = await reservations.reserve(
            user_id, metric, amount, limit, reference, ttl_seconds, now
        )
    except QuotaExceeded as exc:
        raise quota_exceeded(exc, now) from exc
    except ReservationConflict as exc:
        raise reservation_conflict() from exc
    if state.reservation_id is None:
        raise reservation_conflict()
    return QuotaReservationView(
        reservation_id=state.reservation_id,
        metric=metric,
        bucket_date=state.bucket_date,
        used=state.used,
        reserved=state.reserved,
        limit=state.limit,
        remaining=max(0, state.limit - state.used - state.reserved),
        reset_at=state.reset_at,
    )


async def settle_reservation(
    *,
    user_id: UUID,
    reservation_id: UUID,
    commit: bool,
    reservations: UploadQuotaRepository,
    now: datetime,
) -> None:
    """Commit consumed units or release unused ones exactly once."""
    try:
        if commit:
            await reservations.commit(user_id, reservation_id, now)
            return
        await reservations.release(user_id, reservation_id, now)
    except ReservationConflict as exc:
        raise reservation_conflict() from exc


async def acquire_capacity(
    *,
    user_id: UUID,
    metric: UploadMetric,
    amount: int,
    reference: str,
    plan_repo: PlanRepository,
    subscriptions: SubscriptionRepository,
    gauges: UploadQuotaGaugeRepository,
    now: datetime,
) -> QuotaState:
    """Increase a capacity gauge (retained bytes or concurrent uploads)."""
    plan = await resolve_plan(
        user_id=user_id, now=now, plans=plan_repo, subscriptions=subscriptions
    )
    limit = limit_for(plan.upload_limits, metric)
    try:
        return await gauges.acquire(user_id, metric, amount, limit, reference, now)
    except QuotaExceeded as exc:
        raise quota_exceeded(exc, now) from exc


async def close_capacity(
    *,
    user_id: UUID,
    metric: UploadMetric,
    amount: int,
    reference: str,
    gauges: UploadQuotaGaugeRepository,
    now: datetime,
) -> None:
    """Release capacity when a resource is destroyed or rejected."""
    await gauges.close(user_id, metric, amount, reference, now)
