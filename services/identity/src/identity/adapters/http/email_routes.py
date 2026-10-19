"""Email verification and password recovery routes."""

from __future__ import annotations

from diary_security import sha256_digest
from fastapi import APIRouter, Depends, Response, status

from identity.adapters.http.dependencies import get_container, get_repositories
from identity.adapters.http.repositories import Repositories
from identity.adapters.http.schemas_auth import (
    EmailRequest,
    PasswordResetConfirm,
    VerifyEmailRequest,
)
from identity.application.use_cases.email_flows import (
    confirm_password_reset,
    request_password_reset,
    resend_verification,
    verify_email,
)
from identity.container import Container

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify(
    body: VerifyEmailRequest,
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Consume a verification token."""
    await verify_email(
        verifications=repos.verifications,
        accounts=repos.accounts,
        security=repos.security,
        digest=sha256_digest(body.token),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend(
    body: EmailRequest,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, str]:
    """Queue a new verification email without revealing account existence."""
    settings = container.settings
    await resend_verification(
        accounts=repos.accounts,
        verifications=repos.verifications,
        outbox=repos.outbox,
        email_key=settings.email_token_key,
        email_link_base_url=settings.email_link_base_url,
        ttl_hours=settings.verification_ttl_hours,
        email=body.email,
    )
    return {"status": "accepted"}


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def reset_request(
    body: EmailRequest,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> dict[str, str]:
    """Queue a reset email without revealing account existence."""
    settings = container.settings
    await request_password_reset(
        accounts=repos.accounts,
        verifications=repos.verifications,
        outbox=repos.outbox,
        email_key=settings.email_token_key,
        email_link_base_url=settings.email_link_base_url,
        ttl_minutes=settings.reset_ttl_minutes,
        email=body.email,
    )
    return {"status": "accepted"}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def reset_confirm(
    body: PasswordResetConfirm,
    container: Container = Depends(get_container),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Set a new password and revoke every session."""
    await confirm_password_reset(
        accounts=repos.accounts,
        verifications=repos.verifications,
        sessions=repos.sessions,
        security=repos.security,
        hasher=container.hasher,
        token=body.token,
        new_password=body.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
