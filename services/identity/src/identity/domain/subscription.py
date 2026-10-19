"""Plan, subscription and usage reservation entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from diary_contracts.authorization import UsageMetric


def daily_period_start(now: datetime) -> datetime:
    """Quota periods reset at UTC midnight."""
    return datetime(now.year, now.month, now.day, tzinfo=UTC)


class SubscriptionStatus(StrEnum):
    """Provider-independent subscription state."""

    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ReservationState(StrEnum):
    """Quota reservation lifecycle."""

    RESERVED = "reserved"
    FINISHED = "finished"
    ABANDONED = "abandoned"


@dataclass(frozen=True, slots=True)
class Plan:
    """Commercial plan with permission grants and per-period quotas."""

    code: str
    name: str
    permissions: frozenset[str]
    quotas: dict[UsageMetric, int]
    is_default: bool


@dataclass(frozen=True, slots=True)
class Subscription:
    """One user's entitlement at a store provider."""

    user_id: UUID
    plan_code: str
    provider: str
    external_transaction_id: str
    status: SubscriptionStatus
    current_period_end: datetime
    updated_at: datetime

    def grants_access(self, now: datetime) -> bool:
        """Active/grace subscriptions grant access until the period ends."""
        return (
            self.status
            in {
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.GRACE,
                SubscriptionStatus.CANCELLED,
            }
            and self.current_period_end > now
        )


@dataclass(frozen=True, slots=True)
class UsageBucket:
    """Consumption for one user, metric and period start."""

    user_id: UUID
    metric: UsageMetric
    period_start: datetime
    used: int
    limit: int

    @property
    def remaining(self) -> int:
        """Non-negative units still available in the period."""
        return max(0, self.limit - self.used)


@dataclass(frozen=True, slots=True)
class SubscriptionRecord:
    """Stored subscription with encrypted provider token for reconciliation."""

    id: UUID
    user_id: UUID
    plan_code: str
    provider: str
    external_transaction_id: str
    purchase_token_digest: str
    purchase_token_ciphertext: str
    status: SubscriptionStatus
    current_period_end: datetime
