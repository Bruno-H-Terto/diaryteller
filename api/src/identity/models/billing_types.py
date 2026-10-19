"""Provider-neutral billing events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


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
