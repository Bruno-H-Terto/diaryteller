"""Billing value objects, repository alias and provider contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from ..billing_event_repository import PostgresBillingEventRepository
from ..billing_types import StoreEvent, StoreEventType, VerifiedPurchase

BillingEventRepository = PostgresBillingEventRepository

__all__ = [
    "BillingEventRepository",
    "BillingProvider",
    "StoreEvent",
    "StoreEventType",
    "VerifiedPurchase",
]


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
