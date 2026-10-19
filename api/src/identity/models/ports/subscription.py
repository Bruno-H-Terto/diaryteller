"""Plan, subscription and usage persistence aliases."""

from __future__ import annotations

from ..permission_repository import PostgresPlanRepository
from ..subscription_repository import PostgresSubscriptionRepository
from ..usage_repository import PostgresUsageRepository

PlanRepository = PostgresPlanRepository
SubscriptionRepository = PostgresSubscriptionRepository
UsageRepository = PostgresUsageRepository
