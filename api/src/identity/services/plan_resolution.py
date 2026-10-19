"""Resolve the plan that actually applies to a user right now."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from identity.models.ports.subscription import PlanRepository, SubscriptionRepository
from identity.models.subscription import Plan


async def resolve_plan(
    *,
    user_id: UUID,
    now: datetime,
    plans: PlanRepository,
    subscriptions: SubscriptionRepository,
) -> Plan:
    """Use the granted subscription plan, else the configured default plan."""
    subscription = await subscriptions.current(user_id)
    if subscription is not None and subscription.grants_access(now):
        plan = await plans.plan(subscription.plan_code)
        if plan is not None:
            return plan
    return await plans.default_plan()
