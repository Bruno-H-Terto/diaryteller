"""FastAPI dependencies for exchange."""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator
from dataclasses import dataclass

from diary_contracts.authorization import Permission
from diary_contracts.errors import DomainError, ErrorCode
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from exchange.adapters.postgres.context_repository import PostgresContextRepository
from exchange.adapters.postgres.deletion_repository import PostgresDeletionRepository
from exchange.application.ports.identity import Principal
from exchange.container import Container


@dataclass(slots=True)
class Repositories:
    """Repositories bound to the request transaction."""

    contexts: PostgresContextRepository
    deletions: PostgresDeletionRepository


def get_container(request: Request) -> Container:
    """Return the application container."""
    return request.app.state.container


def build_repositories(session: AsyncSession) -> Repositories:
    """Create request-scoped repositories."""
    return Repositories(
        contexts=PostgresContextRepository(session),
        deletions=PostgresDeletionRepository(session),
    )


async def get_session(container: Container = Depends(get_container)) -> AsyncIterator[AsyncSession]:
    """Provide a request transaction committed once."""
    async with container.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_repositories(session: AsyncSession = Depends(get_session)) -> Repositories:
    """Return repositories bound to the request transaction."""
    return build_repositories(session)


async def get_principal(
    authorization: str = Header(default=""),
    x_session_source: str = Header(default="", alias="X-Session-Source"),
    container: Container = Depends(get_container),
) -> Principal:
    """Validate the caller with identity and require exchange access."""
    if not authorization or not x_session_source:
        raise DomainError(ErrorCode.AUTH_INVALID, 401, "Authentication required")
    return await container.identity.authorize(
        authorization=authorization,
        source=x_session_source,
        permission=Permission.EXCHANGE_USE.value,
    )


async def require_internal_service(
    x_internal_service: str = Header(default="", alias="X-Internal-Service"),
    x_internal_token: str = Header(default="", alias="X-Internal-Token"),
    container: Container = Depends(get_container),
) -> str:
    """Authenticate a trusted service caller with its own token."""
    expected = container.settings.internal_secrets.get(x_internal_service)
    if not expected or not hmac.compare_digest(expected, x_internal_token):
        raise DomainError(ErrorCode.AUTH_INVALID, 401, "Internal authentication required")
    return x_internal_service
