"""Internal quota endpoints used by the exchange service."""

from __future__ import annotations

from uuid import UUID

from diary_contracts.quota import (
    QuotaGaugeRequest,
    QuotaReservationView,
    QuotaReserveRequest,
    QuotaResetRequest,
    QuotaSettlementRequest,
    UploadQuota,
)
from fastapi import APIRouter, Depends, Response, status

from identity.controllers.dependencies import get_repositories, require_internal_service
from identity.controllers.repositories import Repositories
from identity.services.common import utcnow
from identity.services.upload_quota import (
    acquire_capacity,
    close_capacity,
    reserve_upload,
    settle_reservation,
    upload_quota_view,
)

router = APIRouter(
    prefix="/internal/upload-quota",
    tags=["internal"],
    dependencies=[Depends(require_internal_service)],
)


@router.get("/snapshot", response_model=UploadQuota)
async def snapshot(owner_id: UUID, repos: Repositories = Depends(get_repositories)) -> UploadQuota:
    """Return the same view the owner sees, for pre-signing validation."""
    return await upload_quota_view(
        user_id=owner_id,
        plan_repo=repos.plans,
        subscriptions=repos.subscriptions,
        gauges=repos.upload_gauges,
        now=utcnow(),
    )


@router.post("/reserve", response_model=QuotaReservationView)
async def reserve(
    body: QuotaReserveRequest, repos: Repositories = Depends(get_repositories)
) -> QuotaReservationView:
    """Reserve metered units before signing an upload."""
    return await reserve_upload(
        user_id=body.owner_id,
        metric=body.metric,
        amount=body.amount,
        reference=body.reference,
        ttl_seconds=body.ttl_seconds,
        plan_repo=repos.plans,
        subscriptions=repos.subscriptions,
        reservations=repos.upload_quota,
        now=utcnow(),
    )


async def _settle(body: QuotaSettlementRequest, repos: Repositories, commit: bool) -> Response:
    await settle_reservation(
        user_id=body.owner_id,
        reservation_id=body.reservation_id,
        commit=commit,
        reservations=repos.upload_quota,
        now=utcnow(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/commit", status_code=status.HTTP_204_NO_CONTENT)
async def commit(
    body: QuotaSettlementRequest, repos: Repositories = Depends(get_repositories)
) -> Response:
    """Consume reserved units after the object was verified."""
    return await _settle(body, repos, True)


@router.post("/release", status_code=status.HTTP_204_NO_CONTENT)
async def release(
    body: QuotaSettlementRequest, repos: Repositories = Depends(get_repositories)
) -> Response:
    """Return reserved units when the upload is abandoned."""
    return await _settle(body, repos, False)


@router.post("/acquire", status_code=status.HTTP_204_NO_CONTENT)
async def acquire(
    body: QuotaGaugeRequest, repos: Repositories = Depends(get_repositories)
) -> Response:
    """Increase a capacity gauge for a newly accepted resource."""
    await acquire_capacity(
        user_id=body.owner_id,
        metric=body.metric,
        amount=body.amount,
        reference=body.reference,
        plan_repo=repos.plans,
        subscriptions=repos.subscriptions,
        gauges=repos.upload_gauges,
        now=utcnow(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/close", status_code=status.HTTP_204_NO_CONTENT)
async def close(
    body: QuotaGaugeRequest, repos: Repositories = Depends(get_repositories)
) -> Response:
    """Release capacity after a resource is destroyed."""
    await close_capacity(
        user_id=body.owner_id,
        metric=body.metric,
        amount=body.amount,
        reference=body.reference,
        gauges=repos.upload_gauges,
        now=utcnow(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/expire")
async def expire(repos: Repositories = Depends(get_repositories)) -> dict[str, int]:
    """Expire stale reservations; safe to run from the maintenance worker."""
    return {"expired": await repos.upload_gauges.expire_stale(utcnow())}


@router.post("/reset-owner", status_code=status.HTTP_204_NO_CONTENT)
async def reset_owner(
    body: QuotaResetRequest, repos: Repositories = Depends(get_repositories)
) -> Response:
    """Drop all quota state for an account being deleted."""
    await repos.upload_gauges.reset_owner(body.owner_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
