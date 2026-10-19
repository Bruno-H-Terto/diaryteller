"""Persistence ports for plans, subscriptions and usage buckets."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from identity.domain.subscription import (
    Plan,
    ReservationState,
    Subscription,
    SubscriptionRecord,
)


class PlanRepository(Protocol):
    """Plans, permissions and role grants."""

    async def default_plan(self) -> Plan:
        """Return the free/default plan."""
        ...

    async def plan(self, code: str) -> Plan | None:
        """Return a plan by code."""
        ...

    async def plans(self) -> list[Plan]:
        """Return all plans for administration/seed checks."""
        ...

    async def user_permissions(self, user_id: UUID) -> set[str]:
        """Return permissions granted by roles, excluding plan grants."""
        ...

    async def upsert_seed(self, plans: list[Plan], role_permissions: dict[str, set[str]]) -> None:
        """Idempotently install reference data (not production user data)."""
        ...


class SubscriptionRepository(Protocol):
    """Subscriptions keyed by user and provider transaction."""

    async def current(self, user_id: UUID) -> Subscription | None:
        """Latest subscription for a user."""
        ...

    async def upsert(
        self, value: Subscription, token_digest: str, token_ciphertext: str, now: datetime
    ) -> None:
        """Store provider state idempotently."""
        ...

    async def record_by_digest(self, digest: str) -> SubscriptionRecord | None:
        """Load the stored record with encrypted token for reconciliation."""
        ...

    async def apply_webhook(
        self, digest: str, status: str, period_end: datetime, now: datetime
    ) -> bool:
        """Apply a normalized webhook state to a known subscription."""
        ...

    async def by_purchase_digest(self, digest: str) -> Subscription | None:
        """Resolve a webhook purchase token to its account."""
        ...

    async def due_for_reconcile(self, before: datetime, limit: int) -> list[Subscription]:
        """Subscriptions whose period end is near."""
        ...


class UsageRepository(Protocol):
    """Atomic usage reservation and finalization."""

    async def reserve(
        self, user_id: UUID, metric: str, amount: int, limit: int, period_start: datetime
    ) -> bool:
        """Atomically reserve units, returning false when quota is exhausted."""
        ...

    async def finalize(
        self,
        user_id: UUID,
        metric: str,
        reserved: int,
        actual: int,
        period_start: datetime,
    ) -> None:
        """Replace a reservation with known consumption."""
        ...

    async def release(
        self, user_id: UUID, metric: str, amount: int, period_start: datetime
    ) -> None:
        """Release unused reserved units without claiming provider cancellation."""
        ...

    async def snapshot(self, user_id: UUID, now: datetime) -> dict[str, tuple[int, int]]:
        """Return used/limit per metric for entitlements."""
        ...

    async def create_reservation(
        self,
        operation_id: UUID,
        user_id: UUID,
        metric: str,
        amount: int,
        period_start: datetime,
        now: datetime,
    ) -> None:
        """Persist the reservation associated with an operation."""
        ...

    async def finish_reservation(
        self, operation_id: UUID, state: ReservationState, now: datetime
    ) -> None:
        """Mark a reservation finished or abandoned."""
        ...
