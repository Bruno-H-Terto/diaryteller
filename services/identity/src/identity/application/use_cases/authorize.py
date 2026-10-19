"""Authorize one permission using persisted state.

Services of AI must call this instead of trusting a JWT or a client-provided
plan. The returned entitlement is authoritative for the operation.
"""

from __future__ import annotations

from datetime import datetime

from diary_contracts.authorization import AuthorizeDecision, Permission

from identity.application.ports.subscription import (
    PlanRepository,
    SubscriptionRepository,
    UsageRepository,
)
from identity.domain.profile import User
from identity.domain.session import Session

from .common import utcnow
from .entitlements import evaluate_entitlement, permission_decision


async def authorize(
    *,
    user: User,
    session: Session,
    permission: Permission,
    plans: PlanRepository,
    subscriptions: SubscriptionRepository,
    usage: UsageRepository,
    now: datetime | None = None,
    request_id: str = "",
) -> AuthorizeDecision:
    """Evaluate account, session, plan and quota state."""
    moment = now or utcnow()
    if not session.is_active(moment):
        view = await evaluate_entitlement(
            user=user,
            session=session,
            plan_repo=plans,
            subscription_repo=subscriptions,
            usage_repo=usage,
            now=moment,
        )
        return AuthorizeDecision(
            allowed=False,
            reason="session_revoked",
            entitlement=view,
            request_id=request_id,
        )
    view = await evaluate_entitlement(
        user=user,
        session=session,
        plan_repo=plans,
        subscription_repo=subscriptions,
        usage_repo=usage,
        now=moment,
        request_id=request_id,
    )
    return permission_decision(
        view,
        permission,
        email_verified=user.email_verified_at is not None,
        request_id=request_id,
    )
