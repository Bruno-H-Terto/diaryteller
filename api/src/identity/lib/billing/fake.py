"""Deterministic billing adapter for local development and tests only.

It is rejected in production by settings validation and by the bootstrap guard.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import UUID

from diary_security import sha256_digest

from identity.models.ports.billing import (
    StoreEvent,
    StoreEventType,
    VerifiedPurchase,
)

PRODUCT_PLANS = {
    "diary_plus_monthly": "plus",
    "diary_pro_monthly": "pro",
}


class FakeBillingProvider:
    """Verify synthetic purchase tokens and HMAC-signed fake webhooks."""

    def __init__(self, signing_key: str) -> None:
        self._key = signing_key.encode()

    async def verify_purchase(
        self, user_id: UUID, product_id: str, purchase_token: str
    ) -> VerifiedPurchase:
        """Accept tokens shaped `<product>:<nonce>` and bind them to the user."""
        plan = PRODUCT_PLANS.get(product_id)
        if plan is None or ":" not in purchase_token:
            raise ValueError("invalid fake purchase")
        nonce = purchase_token.split(":", 1)[1]
        if len(nonce) < 8:
            raise ValueError("invalid fake purchase")
        return VerifiedPurchase(
            transaction_id=f"fake-{sha256_digest(purchase_token)[:24]}",
            product_id=product_id,
            plan_code=plan,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            purchase_token_digest=sha256_digest(purchase_token),
            is_active=True,
        )

    async def lookup_subscription(self, purchase_token: str) -> VerifiedPurchase:
        """Re-verify a synthetic token without account linkage."""
        product = purchase_token.split(":", 1)[0]
        return await self.verify_purchase(UUID(int=0), product, purchase_token)

    async def decode_webhook(self, headers: Mapping[str, str], body: bytes) -> StoreEvent:
        """Validate `X-Fake-Signature` and parse a normalized JSON event."""
        signature = headers.get("x-fake-signature", "")
        expected = hmac.new(self._key, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid webhook signature")
        payload = json.loads(body)
        token = str(payload["purchase_token"])
        return StoreEvent(
            event_id=str(payload["event_id"]),
            event_type=StoreEventType(str(payload["event_type"])),
            transaction_id=str(payload.get("transaction_id", token)),
            product_id=str(payload["product_id"]),
            purchase_token_digest=sha256_digest(token),
            occurred_at=datetime.fromisoformat(str(payload["occurred_at"])),
        )
