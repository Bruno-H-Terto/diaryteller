"""Start an OIDC login transaction for a configured provider."""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from datetime import datetime, timedelta
from uuid import UUID

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.oidc import OidcTransactionView
from diary_security import sha256_digest

from identity.lib.oidc import OidcProviderClient, OidcUnavailable
from identity.models.ports.federation import FederationRepository


def provider_client(providers: Mapping[str, OidcProviderClient], name: str) -> OidcProviderClient:
    """Resolve a configured provider or fail with a documented error."""
    client = providers.get(name)
    if client is None:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Unknown identity provider")
    return client


async def start_oidc(
    *,
    providers: Mapping[str, OidcProviderClient],
    federation: FederationRepository,
    allowed_redirect_uris: list[str],
    provider: str,
    redirect_uri: str,
    device_id: UUID,
    code_challenge: str,
    ttl_seconds: int,
    now: datetime,
) -> OidcTransactionView:
    """Create a transaction and return the URL the app must open."""
    client = provider_client(providers, provider)
    if redirect_uri not in allowed_redirect_uris:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 400, "redirect_uri is not registered")
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    try:
        url = await client.authorization_url(
            redirect_uri=redirect_uri, state=state, nonce=nonce, code_challenge=code_challenge
        )
    except OidcUnavailable as exc:
        raise DomainError(
            ErrorCode.OIDC_PROVIDER_UNAVAILABLE, 503, "Identity provider is unavailable"
        ) from exc
    expires_at = now + timedelta(seconds=ttl_seconds)
    transaction_id = await federation.start_transaction(
        provider=provider,
        state_hash=sha256_digest(state),
        nonce_hash=sha256_digest(nonce),
        redirect_uri=redirect_uri,
        device_id=device_id,
        code_challenge=code_challenge,
        now=now,
        expires_at=expires_at,
    )
    return OidcTransactionView(
        transaction_id=transaction_id,
        authorization_url=url,
        state=state,
        expires_at=expires_at,
    )
