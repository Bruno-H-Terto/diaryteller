"""Tier-based ad policy; paid plans are never asked to watch ads."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from diary_contracts.ad_policy import AdPlacement, AdPolicy

from identity.application.ports.subscription import PlanRepository, SubscriptionRepository

from .plan_resolution import resolve_plan

FREE_PLACEMENTS = [AdPlacement.HOME_BANNER, AdPlacement.POST_SAVE_INTERSTITIAL]


async def ad_policy_view(
    *,
    user_id: UUID,
    plans: PlanRepository,
    subscriptions: SubscriptionRepository,
    now: datetime,
    ads_enabled: bool,
    rewarded_enabled: bool,
    policy_version: str,
) -> AdPolicy:
    """Return the placements allowed for the user's effective plan."""
    plan = await resolve_plan(user_id=user_id, now=now, plans=plans, subscriptions=subscriptions)
    free = plan.is_default
    enabled = ads_enabled and free
    return AdPolicy(
        tier=plan.code,
        enabled=enabled,
        placements=list(FREE_PLACEMENTS) if enabled else [],
        rewarded_enabled=bool(enabled and rewarded_enabled),
        policy_version=policy_version,
    )
