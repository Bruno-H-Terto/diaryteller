"""Public upload quota view for the Android client."""

from __future__ import annotations

from diary_contracts.quota import UploadQuota
from fastapi import APIRouter, Depends

from identity.controllers.dependencies import AuthContext, get_auth, get_repositories
from identity.controllers.repositories import Repositories
from identity.services.common import utcnow
from identity.services.upload_quota import upload_quota_view

router = APIRouter(prefix="/me", tags=["quota"])


@router.get("/upload-quota", response_model=UploadQuota)
async def my_upload_quota(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> UploadQuota:
    """Return plan-derived limits and the counters for the current window."""
    return await upload_quota_view(
        user_id=auth.user.id,
        plan_repo=repos.plans,
        subscriptions=repos.subscriptions,
        gauges=repos.upload_gauges,
        now=utcnow(),
    )
