"""Register an account and queue a single-use verification email.

Existing emails receive the same status without creating or revealing anything.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from identity.adapters.security.email_tokens import create_email_token
from identity.adapters.security.passwords import PasswordHasher
from identity.application.ports.accounts import AccountRepository
from identity.application.ports.notifications import (
    OutboxRepository,
    VerificationTokenRepository,
)
from identity.domain.profile import User

from .common import normalize_email


async def register_account(
    *,
    accounts: AccountRepository,
    verifications: VerificationTokenRepository,
    outbox: OutboxRepository,
    hasher: PasswordHasher,
    email_key: str,
    email_link_base_url: str,
    ttl_hours: int,
    email: str,
    password: str,
    locale: str,
    timezone: str,
    now: datetime,
) -> User | None:
    """Create a user and enqueue verification; return None for existing email."""
    normalized = normalize_email(email)
    existing = await accounts.by_email(normalized)
    if existing is not None:
        await hasher.dummy_verify(password)
        return None
    password_hash = await hasher.hash(password)
    user = await accounts.create(normalized, password_hash, locale, timezone, now)
    token = create_email_token("verify-email", email_key)
    expires_at = now + timedelta(hours=ttl_hours)
    await verifications.create(
        user.id,
        "verify-email",
        token.digest,
        token.ciphertext,
        expires_at,
        now,
    )
    await outbox.append(
        "email.verification",
        {
            "user_id": str(user.id),
            "purpose": "verify-email",
            "token_ciphertext": token.ciphertext,
            "expires_at": expires_at.isoformat(),
            "link_base": email_link_base_url,
            "locale": locale,
        },
        available_at=now,
        dedupe_key=f"email:verify:{token.digest}",
    )
    return user
