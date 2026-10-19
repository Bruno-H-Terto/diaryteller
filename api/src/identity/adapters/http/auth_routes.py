"""Public authentication routes under `/v1/auth`."""

from __future__ import annotations

from diary_contracts.errors import DomainError, ErrorCode
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from identity.adapters.http.dependencies import (
    AuthContext,
    get_auth,
    get_container,
    get_repositories,
    get_session,
    get_source_only,
)
from identity.adapters.http.repositories import Repositories
from identity.adapters.http.schemas_auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    tokens_response,
)
from identity.adapters.security.source_tokens import SourceClaims
from identity.application.use_cases.common import utcnow
from identity.application.use_cases.email_flows import (
    logout,
)
from identity.application.use_cases.login import login
from identity.application.use_cases.refresh import (
    RefreshReuseDetected,
    refresh_session,
)
from identity.application.use_cases.register import register_account
from identity.container import Container

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, str]:
    """Create an account or silently ignore an existing email."""
    settings = container.settings
    await register_account(
        accounts=repos.accounts,
        verifications=repos.verifications,
        outbox=repos.outbox,
        hasher=container.hasher,
        email_key=settings.email_token_key,
        email_link_base_url=settings.email_link_base_url,
        ttl_hours=settings.verification_ttl_hours,
        email=body.email,
        password=body.password,
        locale=body.locale,
        timezone=body.timezone,
        now=utcnow(),
    )
    return {"status": "verification_queued"}


@router.post("/login", response_model=TokenResponse)
async def login_route(
    body: LoginRequest,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> TokenResponse:
    """Authenticate and create a new session for the device."""
    settings = container.settings
    bundle = await login(
        accounts=repos.accounts,
        devices=repos.devices,
        sessions=repos.sessions,
        refresh=repos.refresh,
        throttles=repos.throttles,
        notifications=repos.notifications,
        outbox=repos.outbox,
        push=repos.push,
        security=repos.security,
        hasher=container.hasher,
        access_tokens=container.access_tokens,
        source_tokens=container.source_tokens,
        max_attempts=settings.login_max_attempts,
        window_seconds=settings.login_window_seconds,
        session_max_days=settings.session_max_days,
        refresh_ttl_days=settings.refresh_ttl_days,
        email=body.email,
        password=body.password,
        device_id=body.device_id,
        device_label=body.device_label,
        platform=body.platform,
    )
    return tokens_response(bundle, container.settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_route(
    body: RefreshRequest,
    source: SourceClaims = Depends(get_source_only),
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Rotate refresh credentials; the client must serialize refresh calls."""
    if body.device_id != source.device_id:
        raise DomainError(ErrorCode.SESSION_SOURCE_INVALID, 401, "Session source mismatch")
    try:
        bundle = await refresh_session(
            accounts=repos.accounts,
            sessions=repos.sessions,
            refresh=repos.refresh,
            security=repos.security,
            access_tokens=container.access_tokens,
            source_tokens=container.source_tokens,
            refresh_ttl_days=container.settings.refresh_ttl_days,
            refresh_token=body.refresh_token,
            session_id=source.session_id,
            device_id=source.device_id,
            source_version=source.source_version,
        )
    except RefreshReuseDetected as exc:
        await session.commit()
        raise DomainError(
            ErrorCode.SESSION_REVOKED, 401, "Refresh credential was already used"
        ) from exc
    return tokens_response(bundle, container.settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_route(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Revoke the current session idempotently."""
    await logout(sessions=repos.sessions, security=repos.security, session_id=auth.session.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
