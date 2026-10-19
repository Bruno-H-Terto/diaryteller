"""Purchase verification and authenticated store webhooks."""

from __future__ import annotations

from diary_contracts.errors import DomainError, ErrorCode
from fastapi import APIRouter, Depends, Request

from identity.config.container import Container
from identity.controllers.dependencies import (
    AuthContext,
    get_auth,
    get_container,
    get_repositories,
)
from identity.controllers.repositories import Repositories
from identity.controllers.schemas_auth import VerifyPurchaseRequest
from identity.services.billing import process_webhook, verify_purchase

router = APIRouter(tags=["billing"])

MAX_WEBHOOK_BYTES = 64 * 1024


@router.post("/billing/purchases/verify")
async def verify(
    body: VerifyPurchaseRequest,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> dict[str, object]:
    """Validate a purchase with the store and update the entitlement."""
    return await verify_purchase(
        user=auth.user,
        product_id=body.product_id,
        purchase_token=body.purchase_token,
        provider=container.billing,
        provider_name=container.billing_name,
        subscriptions=repos.subscriptions,
        plans=repos.plans,
        billing_key=container.settings.billing_token_key,
        security=repos.security,
    )


@router.post("/billing/webhooks/{provider}")
async def webhook(
    provider: str,
    request: Request,
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> dict[str, str]:
    """Authenticate and process a store event; duplicates are safe."""
    if provider != container.billing_name:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Unknown provider")
    body = await request.body()
    if len(body) > MAX_WEBHOOK_BYTES:
        raise DomainError(ErrorCode.MEDIA_TOO_LARGE, 413, "Webhook payload too large")
    outcome = await process_webhook(
        provider=container.billing,
        provider_name=container.billing_name,
        headers={key.lower(): value for key, value in request.headers.items()},
        body=body,
        events=repos.billing_events,
        subscriptions=repos.subscriptions,
        outbox=repos.outbox,
        security=repos.security,
    )
    return {"status": outcome}
