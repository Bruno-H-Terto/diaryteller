"""Email verification, resend and password recovery flows.

Existence of an account is never revealed by request/resend responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from diary_contracts.errors import DomainError, ErrorCode
from diary_messaging import EMAIL_EVENTS
from diary_security import encrypt_json, sha256_digest

from identity.adapters.security.email_tokens import create_email_token
from identity.adapters.security.passwords import PasswordHasher
from identity.application.ports.accounts import AccountRepository
from identity.application.ports.notifications import (
    OutboxRepository,
    SecurityRepository,
    VerificationTokenRepository,
)
from identity.application.ports.sessions import SessionRepository

from .common import normalize_email, utcnow


def _invalid_token() -> DomainError:
    return DomainError(ErrorCode.TOKEN_INVALID, 400, "Token is invalid or expired")


async def verify_email(
    *,
    verifications: VerificationTokenRepository,
    accounts: AccountRepository,
    security: SecurityRepository,
    digest: str,
    now: datetime | None = None,
) -> None:
    """Consume a verification token and mark the email verified."""
    moment = now or utcnow()
    user_id = await verifications.consume("verify-email", digest, moment)
    if user_id is None:
        raise _invalid_token()
    await accounts.mark_email_verified(user_id, moment)
    await security.record(
        user_id=user_id,
        session_id=None,
        event_type="email.verified",
        reference=None,
        now=moment,
    )


async def _issue_email(
    *,
    accounts: AccountRepository,
    verifications: VerificationTokenRepository,
    outbox: OutboxRepository,
    email_key: str,
    email_link_base_url: str,
    purpose: str,
    ttl: timedelta,
    email: str,
    now: datetime,
    event_type: str,
) -> None:
    user = await accounts.by_email(normalize_email(email))
    if user is None:
        return
    if purpose == "verify-email" and user.email_verified_at is not None:
        return
    await verifications.invalidate_user(user.id, purpose, now)
    token = create_email_token(purpose, email_key)
    expires_at = now + ttl
    await verifications.create(user.id, purpose, token.digest, token.ciphertext, expires_at, now)
    await outbox.append(
        event_type,
        {
            "user_id": str(user.id),
            "purpose": purpose,
            "token_ciphertext": token.ciphertext,
            "expires_at": expires_at.isoformat(),
            "link_base": email_link_base_url,
            "recipient_ciphertext": encrypt_json({"email": normalize_email(email)}, email_key),
        },
        available_at=now,
        dedupe_key=f"email:{purpose}:{token.digest}",
        topic=EMAIL_EVENTS,
    )


async def resend_verification(
    *,
    accounts: AccountRepository,
    verifications: VerificationTokenRepository,
    outbox: OutboxRepository,
    email_key: str,
    email_link_base_url: str,
    ttl_hours: int,
    email: str,
    now: datetime | None = None,
) -> None:
    """Queue a new verification email when applicable."""
    moment = now or utcnow()
    await _issue_email(
        accounts=accounts,
        verifications=verifications,
        outbox=outbox,
        email_key=email_key,
        email_link_base_url=email_link_base_url,
        purpose="verify-email",
        ttl=timedelta(hours=ttl_hours),
        email=email,
        now=moment,
        event_type="email.verification",
    )


async def request_password_reset(
    *,
    accounts: AccountRepository,
    verifications: VerificationTokenRepository,
    outbox: OutboxRepository,
    email_key: str,
    email_link_base_url: str,
    ttl_minutes: int,
    email: str,
    now: datetime | None = None,
) -> None:
    """Queue a reset email when the account exists."""
    moment = now or utcnow()
    await _issue_email(
        accounts=accounts,
        verifications=verifications,
        outbox=outbox,
        email_key=email_key,
        email_link_base_url=email_link_base_url,
        purpose="password-reset",
        ttl=timedelta(minutes=ttl_minutes),
        email=email,
        now=moment,
        event_type="email.password_reset",
    )


async def confirm_password_reset(
    *,
    accounts: AccountRepository,
    verifications: VerificationTokenRepository,
    sessions: SessionRepository,
    security: SecurityRepository,
    hasher: PasswordHasher,
    token: str,
    new_password: str,
    now: datetime | None = None,
) -> None:
    """Consume a reset token, change the password and revoke all sessions."""
    moment = now or utcnow()
    digest = sha256_digest(token)
    user_id = await verifications.consume("password-reset", digest, moment)
    if user_id is None:
        raise _invalid_token()
    password_hash = await hasher.hash(new_password)
    await accounts.update_password(user_id, password_hash, moment)
    await sessions.revoke_all(user_id, "password_reset", moment)
    await security.record(
        user_id=user_id,
        session_id=None,
        event_type="password.reset",
        reference=None,
        now=moment,
    )


async def logout(
    *,
    sessions: SessionRepository,
    security: SecurityRepository,
    session_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    """Revoke the current session idempotently."""
    moment = now or utcnow()
    await sessions.revoke(session_id, "logout", moment)
    await security.record(
        user_id=None,
        session_id=session_id,
        event_type="session.logout",
        reference=None,
        now=moment,
    )
