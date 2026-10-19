"""FastAPI dependencies: database session, caller identity and service auth."""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

from diary_contracts.errors import DomainError, ErrorCode
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from identity.adapters.postgres.session_repository import PostgresSessionRepository
from identity.adapters.security.access_tokens import AccessClaims, TokenInvalid
from identity.adapters.security.source_tokens import SourceClaims, SourceInvalid
from identity.container import Container
from identity.domain.profile import User
from identity.domain.session import Session


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Validated user, session and tokens for one request."""

    user: User
    session: Session
    access: AccessClaims
    source: SourceClaims


def get_container(request: Request) -> Container:
    """Return the application container."""
    return request.app.state.container


async def get_session(
    container: Container = Depends(get_container),
) -> AsyncIterator[AsyncSession]:
    """Provide a request-scoped session and commit exactly once."""
    async with container.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _unauthorized(code: ErrorCode, title: str) -> DomainError:
    return DomainError(code, 401, title)


async def get_auth(
    authorization: str = Header(default=""),
    x_session_source: str = Header(default="", alias="X-Session-Source"),
    session: AsyncSession = Depends(get_session),
    container: Container = Depends(get_container),
) -> AuthContext:
    """Validate JWT + source and bind them to the persisted session."""
    if not authorization.lower().startswith("bearer ") or not x_session_source:
        raise _unauthorized(ErrorCode.AUTH_INVALID, "Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = container.access_tokens.verify(token)
        source = container.source_tokens.verify(x_session_source)
    except (TokenInvalid, SourceInvalid) as exc:
        raise _unauthorized(ErrorCode.AUTH_INVALID, "Invalid credentials") from exc
    if claims.session_id != source.session_id:
        raise _unauthorized(ErrorCode.SESSION_SOURCE_INVALID, "Session source mismatch")
    store = PostgresSessionRepository(session)
    persisted = await store.by_id(claims.session_id)
    now = datetime.now(UTC)
    if persisted is None or persisted.user_id != claims.user_id:
        raise _unauthorized(ErrorCode.SESSION_REVOKED, "Session is not active")
    if not persisted.is_active(now):
        raise _unauthorized(ErrorCode.SESSION_REVOKED, "Session is not active")
    if persisted.device_id != source.device_id:
        raise _unauthorized(ErrorCode.SESSION_SOURCE_INVALID, "Session source mismatch")
    if persisted.source_version != source.source_version:
        raise _unauthorized(ErrorCode.SESSION_SOURCE_INVALID, "Session source is outdated")
    from identity.adapters.postgres.account_repository import PostgresAccountRepository

    user = await PostgresAccountRepository(session).by_id(claims.user_id)
    if user is None:
        raise _unauthorized(ErrorCode.SESSION_REVOKED, "Session is not active")
    if (now - persisted.last_seen_at).total_seconds() > 120:
        await store.touch(persisted.id, now)
    return AuthContext(user=user, session=persisted, access=claims, source=source)


async def require_internal_service(
    x_internal_service: str = Header(default="", alias="X-Internal-Service"),
    x_internal_token: str = Header(default="", alias="X-Internal-Token"),
    container: Container = Depends(get_container),
) -> str:
    """Authenticate a trusted service caller with its own token."""
    expected = container.settings.identity_internal_secrets.get(x_internal_service)
    if not expected or not hmac.compare_digest(expected, x_internal_token):
        raise _unauthorized(ErrorCode.AUTH_INVALID, "Internal authentication required")
    return x_internal_service


async def get_source_only(
    x_session_source: str = Header(default="", alias="X-Session-Source"),
    container: Container = Depends(get_container),
) -> SourceClaims:
    """Validate only the encrypted source for refresh (JWT may be expired)."""
    if not x_session_source:
        raise _unauthorized(ErrorCode.SESSION_SOURCE_INVALID, "Session source required")
    try:
        return container.source_tokens.verify(x_session_source)
    except SourceInvalid as exc:
        raise _unauthorized(ErrorCode.SESSION_SOURCE_INVALID, "Invalid session source") from exc


async def get_repositories(
    session: AsyncSession = Depends(get_session),
):
    """Return repositories bound to the request transaction."""
    from identity.adapters.http.repositories import build_repositories

    return build_repositories(session)
