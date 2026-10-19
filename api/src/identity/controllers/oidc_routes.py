"""Public OIDC routes: start transaction, exchange code, link account."""

from __future__ import annotations

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.oidc import (
    OidcExchangeRequest,
    OidcLinkRequest,
    OidcStartRequest,
    OidcTransactionView,
)
from diary_security import sha256_digest
from fastapi import APIRouter, Depends, Response, status

from identity.config.container import Container
from identity.controllers.dependencies import (
    AuthContext,
    get_auth,
    get_container,
    get_repositories,
)
from identity.controllers.repositories import Repositories
from identity.controllers.schemas_auth import TokenResponse, tokens_response
from identity.services.common import locked_out, utcnow
from identity.services.oidc_login import exchange_oidc, link_oidc
from identity.services.oidc_start import start_oidc
from identity.services.session_issuance import SessionIssuer

router = APIRouter(prefix="/auth/oidc", tags=["auth"])


def _require_enabled(container: Container) -> None:
    if not container.settings.oidc_enabled:
        raise DomainError(ErrorCode.FEATURE_DISABLED, 404, "OIDC is not enabled")


def _issuer(container: Container, repos: Repositories) -> SessionIssuer:
    settings = container.settings
    return SessionIssuer(
        devices=repos.devices,
        sessions=repos.sessions,
        refresh=repos.refresh,
        notifications=repos.notifications,
        outbox=repos.outbox,
        push=repos.push,
        security=repos.security,
        access_tokens=container.access_tokens,
        source_tokens=container.source_tokens,
        session_max_days=settings.session_max_days,
        refresh_ttl_days=settings.refresh_ttl_days,
    )


@router.post("/transactions", response_model=OidcTransactionView)
async def start_transaction(
    body: OidcStartRequest,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> OidcTransactionView:
    """Create a short-lived transaction and return the browser URL."""
    _require_enabled(container)
    settings = container.settings
    now = utcnow()
    throttle_key = sha256_digest(f"oidc-start:{body.device_id}")
    if await repos.throttles.locked(throttle_key, now):
        raise locked_out()
    view = await start_oidc(
        providers=container.oidc_providers,
        federation=repos.federation,
        allowed_redirect_uris=settings.oidc_allowed_redirect_uris,
        provider=body.provider,
        redirect_uri=body.redirect_uri,
        device_id=body.device_id,
        code_challenge=body.code_challenge,
        ttl_seconds=settings.oidc_transaction_ttl_seconds,
        now=now,
    )
    await repos.throttles.record_failure(
        throttle_key, now, settings.login_window_seconds, settings.login_max_attempts
    )
    return view


@router.post("/exchange", response_model=TokenResponse)
async def exchange(
    body: OidcExchangeRequest,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> TokenResponse:
    """Exchange the authorization code server-side for a session."""
    _require_enabled(container)
    codec = container.oidc_link_tokens
    if codec is None:
        raise DomainError(ErrorCode.FEATURE_DISABLED, 404, "OIDC is not enabled")
    bundle = await exchange_oidc(
        providers=container.oidc_providers,
        federation=repos.federation,
        accounts=repos.accounts,
        issuer=_issuer(container, repos),
        link_tokens=codec,
        transaction_id=body.transaction_id,
        code=body.code,
        state=body.state,
        code_verifier=body.code_verifier,
        now=utcnow(),
    )
    return tokens_response(bundle, container.settings)


@router.post("/link", status_code=status.HTTP_204_NO_CONTENT)
async def link(
    body: OidcLinkRequest,
    auth: AuthContext = Depends(get_auth),
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Link the provider identity to the authenticated account."""
    _require_enabled(container)
    codec = container.oidc_link_tokens
    if codec is None:
        raise DomainError(ErrorCode.FEATURE_DISABLED, 404, "OIDC is not enabled")
    await link_oidc(
        user=auth.user,
        link_token=body.link_token,
        link_tokens=codec,
        federation=repos.federation,
        now=utcnow(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
