"""Purchase verification, webhook deduplication and entitlement updates."""

from __future__ import annotations

from datetime import datetime

from diary_contracts.errors import DomainError, ErrorCode
from diary_security import encrypt_json

from identity.models.ports.billing import (
    BillingEventRepository,
    BillingProvider,
    StoreEventType,
)
from identity.models.ports.notifications import OutboxRepository, SecurityRepository
from identity.models.ports.subscription import PlanRepository, SubscriptionRepository
from identity.models.profile import User
from identity.models.subscription import Subscription, SubscriptionStatus

from .common import utcnow


async def verify_purchase(
    *,
    user: User,
    product_id: str,
    purchase_token: str,
    provider: BillingProvider,
    provider_name: str,
    subscriptions: SubscriptionRepository,
    plans: PlanRepository,
    billing_key: str,
    security: SecurityRepository,
    now: datetime | None = None,
) -> dict[str, object]:
    """Verify with the store, bind the transaction and update entitlement."""
    moment = now or utcnow()
    verified = await provider.verify_purchase(user.id, product_id, purchase_token)
    plan = await plans.plan(verified.plan_code)
    if plan is None or not verified.is_active:
        raise DomainError(
            ErrorCode.SUBSCRIPTION_REQUIRED, 409, "Purchase is not active for a known plan"
        )
    existing = await subscriptions.record_by_digest(verified.purchase_token_digest)
    if existing is not None and existing.user_id != user.id:
        raise DomainError(ErrorCode.FORBIDDEN, 403, "Purchase is already linked")
    ciphertext = encrypt_json({"token": purchase_token, "provider": provider_name}, billing_key)
    await subscriptions.upsert(
        Subscription(
            user_id=user.id,
            plan_code=verified.plan_code,
            provider=provider_name,
            external_transaction_id=verified.transaction_id,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=verified.expires_at,
            updated_at=moment,
        ),
        verified.purchase_token_digest,
        ciphertext,
        moment,
    )
    await security.record(
        user_id=user.id,
        session_id=None,
        event_type="billing.purchase_verified",
        reference=verified.plan_code,
        now=moment,
    )
    return {
        "plan_code": verified.plan_code,
        "expires_at": verified.expires_at,
        "provider": provider_name,
    }


async def process_webhook(
    *,
    provider: BillingProvider,
    provider_name: str,
    headers: dict[str, str],
    body: bytes,
    events: BillingEventRepository,
    subscriptions: SubscriptionRepository,
    outbox: OutboxRepository,
    security: SecurityRepository,
    now: datetime | None = None,
) -> str:
    """Authenticate, deduplicate and apply a store event."""
    moment = now or utcnow()
    try:
        event = await provider.decode_webhook(headers, body)
    except Exception as exc:
        raise DomainError(ErrorCode.AUTH_INVALID, 401, "Invalid webhook") from exc
    event_id = await events.claim(provider_name, event, moment)
    if event_id is None:
        return "duplicate"
    record = await subscriptions.record_by_digest(event.purchase_token_digest)
    if record is None:
        await events.mark(event_id, "unlinked", moment)
        return "unlinked"
    if event.event_type in {StoreEventType.PURCHASE, StoreEventType.RENEWAL}:
        status = SubscriptionStatus.ACTIVE
        period_end = record.current_period_end
        await outbox.append(
            "billing.reconcile",
            {"purchase_digest": event.purchase_token_digest},
            available_at=moment,
            dedupe_key=f"billing:reconcile:{event.event_id}",
        )
    elif event.event_type is StoreEventType.CANCEL:
        status = SubscriptionStatus.CANCELLED
        period_end = record.current_period_end
    elif event.event_type is StoreEventType.REFUND:
        status = SubscriptionStatus.REFUNDED
        period_end = min(record.current_period_end, event.occurred_at)
    else:
        status = SubscriptionStatus.EXPIRED
        period_end = min(record.current_period_end, event.occurred_at)
    await subscriptions.apply_webhook(event.purchase_token_digest, status.value, period_end, moment)
    await events.mark(event_id, status.value, moment)
    await security.record(
        user_id=record.user_id,
        session_id=None,
        event_type="billing.webhook",
        reference=status.value,
        now=moment,
    )
    return status.value
