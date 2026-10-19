"""Google Play purchase verification and RTDN webhook authentication.

The adapter talks to Android Publisher over TLS and validates Pub/Sub OIDC
tokens. All blocking Google client calls run in worker threads.
"""

from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from diary_security import hmac_digest, sha256_digest
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2 import id_token, service_account

from identity.models.ports.billing import (
    StoreEvent,
    StoreEventType,
    VerifiedPurchase,
)

_API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
_EVENT_TYPES = {
    1: StoreEventType.RENEWAL,
    2: StoreEventType.RENEWAL,
    3: StoreEventType.CANCEL,
    4: StoreEventType.PURCHASE,
    5: StoreEventType.CANCEL,
    6: StoreEventType.RENEWAL,
    7: StoreEventType.RENEWAL,
    12: StoreEventType.REFUND,
    13: StoreEventType.EXPIRE,
}


class GooglePlayBillingProvider:
    """Real store adapter for the chosen Google Play ecosystem."""

    def __init__(
        self,
        *,
        package_name: str,
        service_account_json: str,
        products: dict[str, str],
        pubsub_audience: str,
        pubsub_service_account: str,
        account_link_salt: str,
    ) -> None:
        self._package = package_name
        self._products = products
        self._audience = pubsub_audience
        self._service_account_email = pubsub_service_account
        self._salt = account_link_salt
        self._credentials = service_account.Credentials.from_service_account_info(
            json.loads(service_account_json),
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )

    def _fetch(self, purchase_token: str) -> dict[str, Any]:
        session = AuthorizedSession(self._credentials)
        try:
            response = session.get(
                f"{_API}/{self._package}/purchases/subscriptionsv2/tokens/{purchase_token}",
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        finally:
            session.close()

    def _normalize(self, data: dict[str, Any], purchase_token: str) -> VerifiedPurchase:
        line_items = data.get("lineItems") or []
        if not line_items:
            raise ValueError("purchase has no line item")
        product_id = str(line_items[0].get("productId", ""))
        plan = self._products.get(product_id)
        if plan is None:
            raise ValueError("unknown product")
        expiry = datetime.fromisoformat(str(line_items[0]["expiryTime"]).replace("Z", "+00:00"))
        state = str(data.get("subscriptionState", ""))
        active = state in {"SUBSCRIPTION_STATE_ACTIVE", "SUBSCRIPTION_STATE_IN_GRACE_PERIOD"}
        transaction = str(data.get("latestOrderId") or sha256_digest(purchase_token)[:32])
        return VerifiedPurchase(
            transaction_id=transaction,
            product_id=product_id,
            plan_code=plan,
            expires_at=expiry,
            purchase_token_digest=sha256_digest(purchase_token),
            is_active=active,
        )

    def _expected_account(self, user_id: UUID) -> str:
        return hmac_digest(self._salt, {"user_id": str(user_id)})[:64]

    async def verify_purchase(
        self, user_id: UUID, product_id: str, purchase_token: str
    ) -> VerifiedPurchase:
        """Fetch subscription state and require the account linkage."""
        data = await asyncio.to_thread(self._fetch, purchase_token)
        purchase = self._normalize(data, purchase_token)
        if purchase.product_id != product_id:
            raise ValueError("product mismatch")
        identifier = (data.get("externalAccountIdentifiers") or {}).get(
            "obfuscatedExternalAccountId"
        )
        if identifier is None or identifier != self._expected_account(user_id):
            raise ValueError("purchase is not linked to this account")
        return purchase

    async def lookup_subscription(self, purchase_token: str) -> VerifiedPurchase:
        """Re-read state for reconciliation."""
        data = await asyncio.to_thread(self._fetch, purchase_token)
        return self._normalize(data, purchase_token)

    def _verify_oidc(self, token: str) -> None:
        claims = id_token.verify_oauth2_token(token, Request(), audience=self._audience)
        if claims.get("email") != self._service_account_email:
            raise ValueError("invalid webhook identity")

    async def decode_webhook(self, headers: Mapping[str, str], body: bytes) -> StoreEvent:
        """Validate Pub/Sub OIDC and normalize the RTDN payload."""
        authorization = headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            raise ValueError("missing webhook bearer token")
        await asyncio.to_thread(self._verify_oidc, authorization.split(" ", 1)[1])
        envelope = json.loads(body)
        message = envelope.get("message") or {}
        data = json.loads(base64.b64decode(message["data"]))
        notification = data.get("subscriptionNotification")
        if not notification:
            raise ValueError("unsupported notification")
        token = str(notification["purchaseToken"])
        occurred = datetime.fromtimestamp(int(data["eventTimeMillis"]) / 1000, UTC)
        event_type = _EVENT_TYPES.get(int(notification["notificationType"]))
        if event_type is None:
            raise ValueError("unsupported notification type")
        digest = sha256_digest(token)
        return StoreEvent(
            event_id=str(message.get("messageId", digest)),
            event_type=event_type,
            transaction_id=digest,
            product_id=str(notification.get("subscriptionId", "")),
            purchase_token_digest=digest,
            occurred_at=occurred,
        )
