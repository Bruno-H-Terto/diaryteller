"""OIDC login with PKCE, one-time transactions and explicit account linking.

A verified provider email never merges accounts by itself: the caller must first
authenticate the existing account, then present the encrypted link token.
"""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from diary_contracts.authorization import AccountStatus
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.oidc import OidcConflictDetails
from diary_security import sha256_digest

from identity.adapters.oidc import (
    OidcIdentity,
    OidcInvalidToken,
    OidcProviderClient,
    OidcUnavailable,
)
from identity.adapters.security.oidc_link_tokens import LinkTokenInvalid, OidcLinkTokenCodec
from identity.application.ports.accounts import AccountRepository
from identity.application.ports.federation import FederationRepository
from identity.domain.profile import User

from .common import IssuedSession, normalize_email
from .oidc_start import provider_client
from .session_issuance import SessionIssuer

DEFAULT_LOCALE = "pt-BR"
DEFAULT_TIMEZONE = "UTC"


def _transaction_invalid() -> DomainError:
    return DomainError(
        ErrorCode.OIDC_TRANSACTION_INVALID, 400, "OIDC transaction is invalid or expired"
    )


async def exchange_oidc(
    *,
    providers: Mapping[str, OidcProviderClient],
    federation: FederationRepository,
    accounts: AccountRepository,
    issuer: SessionIssuer,
    link_tokens: OidcLinkTokenCodec,
    transaction_id: UUID,
    code: str,
    state: str,
    code_verifier: str,
    now: datetime,
) -> IssuedSession:
    """Exchange the authorization code server-side and start a session."""
    transaction = await federation.lock_transaction(transaction_id, now)
    if transaction is None:
        raise _transaction_invalid()
    if not hmac.compare_digest(transaction.state_hash, sha256_digest(state)):
        raise _transaction_invalid()
    client = provider_client(providers, transaction.provider)
    try:
        identity = await client.exchange(
            code=code,
            redirect_uri=transaction.redirect_uri,
            code_verifier=code_verifier,
            nonce_hash=transaction.nonce_hash,
        )
    except OidcUnavailable as exc:
        raise DomainError(
            ErrorCode.OIDC_PROVIDER_UNAVAILABLE, 503, "Identity provider is unavailable"
        ) from exc
    except OidcInvalidToken as exc:
        raise _transaction_invalid() from exc
    if identity.email is None or not identity.email_verified:
        raise DomainError(
            ErrorCode.EMAIL_NOT_VERIFIED,
            403,
            "The provider did not verify this email",
            details={"can_resend": False},
        )
    linked = await federation.find(identity.issuer, identity.subject)
    if linked is not None:
        user = await accounts.by_id(linked.user_id)
        if user is None or user.status is not AccountStatus.ACTIVE:
            raise DomainError(ErrorCode.ACCOUNT_DISABLED, 403, "Account is not active")
        await federation.consume_transaction(transaction.id, user.id, now)
        await federation.touch(linked.id, now)
        return await _issue(issuer, user.id, transaction.device_id, now)
    existing = await accounts.by_email(normalize_email(identity.email))
    if existing is not None:
        raise _link_required(link_tokens, identity, now)
    user = await accounts.create_federated(
        normalize_email(identity.email), DEFAULT_LOCALE, DEFAULT_TIMEZONE, now
    )
    await federation.link(
        user.id,
        issuer=identity.issuer,
        subject=identity.subject,
        provider=identity.provider,
        email=identity.email,
        now=now,
    )
    await federation.consume_transaction(transaction.id, user.id, now)
    return await _issue(issuer, user.id, transaction.device_id, now)


async def link_oidc(
    *,
    user: User,
    link_token: str,
    link_tokens: OidcLinkTokenCodec,
    federation: FederationRepository,
    now: datetime,
) -> None:
    """Bind the provider identity after the user proved the existing account."""
    try:
        claims = link_tokens.verify(link_token, now)
    except LinkTokenInvalid as exc:
        raise DomainError(ErrorCode.TOKEN_INVALID, 401, "Link token is invalid") from exc
    if normalize_email(user.email) != claims.email:
        raise DomainError(
            ErrorCode.ACCOUNT_LINK_REQUIRED, 409, "Sign in with the matching account first"
        )
    linked = await federation.find(claims.issuer, claims.subject)
    if linked is not None and linked.user_id != user.id:
        raise DomainError(ErrorCode.ACCOUNT_LINK_REQUIRED, 409, "Identity is already linked")
    if linked is None:
        await federation.link(
            user.id,
            issuer=claims.issuer,
            subject=claims.subject,
            provider=claims.provider,
            email=claims.email,
            now=now,
        )


def _link_required(
    link_tokens: OidcLinkTokenCodec, identity: OidcIdentity, now: datetime
) -> DomainError:
    if identity.email is None:
        raise DomainError(ErrorCode.EMAIL_NOT_VERIFIED, 403, "Email is not verified")
    token = link_tokens.issue(
        provider=identity.provider,
        issuer=identity.issuer,
        subject=identity.subject,
        email=identity.email,
        now=now,
    )
    details = OidcConflictDetails(provider=identity.provider, link_token=token)
    return DomainError(
        ErrorCode.ACCOUNT_LINK_REQUIRED,
        409,
        "An account with this email already exists",
        details=details.model_dump(mode="json"),
    )


async def _issue(
    issuer: SessionIssuer, user_id: UUID, device_id: UUID, now: datetime
) -> IssuedSession:
    return await issuer.issue(
        user_id=user_id,
        device_id=device_id,
        device_label=None,
        platform="oidc",
        now=now,
    )
