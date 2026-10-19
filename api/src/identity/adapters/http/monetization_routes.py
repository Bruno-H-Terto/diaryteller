"""Ad policy exposed to the Android client."""

from __future__ import annotations

from diary_contracts.ad_policy import AdPolicy
from fastapi import APIRouter, Depends

from identity.adapters.http.dependencies import (
    AuthContext,
    get_auth,
    get_container,
    get_repositories,
)
from identity.adapters.http.repositories import Repositories
from identity.application.use_cases.ad_policy import ad_policy_view
from identity.application.use_cases.common import utcnow
from identity.container import Container

router = APIRouter(prefix="/monetization", tags=["monetization"])


@router.get("/ad-policy", response_model=AdPolicy)
async def ad_policy(
    auth: AuthContext = Depends(get_auth),
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> AdPolicy:
    """Return the placements allowed for the effective plan."""
    settings = container.settings
    return await ad_policy_view(
        user_id=auth.user.id,
        plans=repos.plans,
        subscriptions=repos.subscriptions,
        now=utcnow(),
        ads_enabled=settings.ads_enabled,
        rewarded_enabled=settings.rewarded_ads_enabled,
        policy_version=settings.ad_policy_version,
    )
