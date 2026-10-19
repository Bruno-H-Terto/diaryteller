"""Billing provider port and provider-neutral purchase events."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class StoreEventType(StrEnum):
    """Normalized store events relevant to entitlements."""

    PURCHASE = "purchase"
    RENEWAL = "renewal"
    CANCEL = "cancel"
    EXPIRE = "expire"
    REFUND = "refund"


@dataclass(frozen=True, slots=True)
class VerifiedPurchase:
    """Server-verified purchase linked to an account."""

    transaction_id: str
    product_id: str
    plan_code: str
    expires_at: datetime
    purchase_token_digest: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class StoreEvent:
    """Authenticated webhook event after provider signature verification."""

    event_id: str
    event_type: StoreEventType
    transaction_id: str
    product_id: str
    purchase_token_digest: str
    occurred_at: datetime


class BillingProvider(Protocol):
    """Store verification and webhook authentication."""

    async def verify_purchase(
        self, user_id: UUID, product_id: str, purchase_token: str
    ) -> VerifiedPurchase:
        """Ask the store whether the token is valid and active."""
        ...

    async def decode_webhook(self, headers: Mapping[str, str], body: bytes) -> StoreEvent:
        """Authenticate and normalize a webhook event."""
        ...

    async def lookup_subscription(self, purchase_token: str) -> VerifiedPurchase:
        """Re-read provider state for reconciliation."""
        ...


class BillingEventRepository(Protocol):
    """Webhook deduplication ledger."""

    async def claim(self, provider: str, event: StoreEvent, now: datetime) -> UUID | None:
        """Claim an event id, returning None for duplicates."""
        ...

    async def mark(self, event_id: UUID, outcome: str, now: datetime) -> None:
        """Record the processing outcome."""
        ...
