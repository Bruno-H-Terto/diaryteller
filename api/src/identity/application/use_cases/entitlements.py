"""Compute the authoritative entitlement view for one session.

The plan comes from stored subscriptions, never from request data. Permissions
combine roles and the effective plan; quotas are per UTC day.
"""

from __future__ import annotations

from datetime import datetime

from diary_contracts.authorization import (
    AuthorizeDecision,
    EntitlementView,
    Permission,
    UsageMetric,
)

from identity.application.ports.subscription import (
    PlanRepository,
    SubscriptionRepository,
    UsageRepository,
)
from identity.domain.profile import User
from identity.domain.session import Session

from .plan_resolution import resolve_plan


async def evaluate_entitlement(
    *,
    user: User,
    session: Session,
    plan_repo: PlanRepository,
    subscription_repo: SubscriptionRepository,
    usage_repo: UsageRepository,
    now: datetime,
    request_id: str = "",
) -> EntitlementView:
    """Materialize plan, permissions and remaining quota for a user/session."""
    subscription = await subscription_repo.current(user.id)
    plan = await resolve_plan(
        user_id=user.id, now=now, plans=plan_repo, subscriptions=subscription_repo
    )
    role_permissions = await plan_repo.user_permissions(user.id)
    permissions = sorted(set(role_permissions) | set(plan.permissions))
    snapshot = await usage_repo.snapshot(user.id, now)
    remaining: dict[UsageMetric, int] = {}
    for metric, limit in plan.quotas.items():
        used, current_limit = snapshot.get(metric.value, (0, limit))
        remaining[metric] = max(0, current_limit - used)
    return EntitlementView(
        user_id=user.id,
        session_id=session.id,
        account_status=user.status,
        plan_code=plan.code,
        plan_expires_at=subscription.current_period_end if subscription else None,
        permissions=[Permission(value) for value in permissions],
        quotas=plan.quotas,
        quota_remaining=remaining,
        source_version=session.source_version,
        evaluated_at=now,
    )


def permission_decision(
    view: EntitlementView,
    permission: Permission,
    *,
    email_verified: bool,
    request_id: str = "",
) -> AuthorizeDecision:
    """Combine account state, session state and the requested permission."""
    reason: str | None = None
    if not email_verified:
        reason = "email_not_verified"
    elif view.account_status.value != "active":
        reason = "account_disabled"
    elif permission not in view.permissions:
        reason = "permission_missing"
    return AuthorizeDecision(
        allowed=reason is None,
        reason=reason,
        entitlement=view,
        request_id=request_id,
    )
