"""Authenticate a device and create a persisted, revocable session.

The notification content is generic and contains no diary data. The refresh
credential is stored as a digest only.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.authorization import AccountStatus
from diary_contracts.errors import DomainError, ErrorCode
from diary_security import sha256_digest

from identity.adapters.security.access_tokens import AccessTokenIssuer
from identity.adapters.security.passwords import PasswordHasher
from identity.adapters.security.source_tokens import SourceTokenCodec
from identity.application.ports.accounts import (
    AccountRepository,
    DeviceRepository,
    ThrottleRepository,
)
from identity.application.ports.notifications import (
    NotificationRepository,
    OutboxRepository,
    SecurityRepository,
)
from identity.application.ports.sessions import RefreshRepository, SessionRepository

from .common import IssuedSession, invalid_credentials, locked_out, normalize_email, utcnow
from .session_issuance import issue_session


async def login(
    *,
    accounts: AccountRepository,
    devices: DeviceRepository,
    sessions: SessionRepository,
    refresh: RefreshRepository,
    throttles: ThrottleRepository,
    notifications: NotificationRepository,
    outbox: OutboxRepository,
    security: SecurityRepository,
    hasher: PasswordHasher,
    access_tokens: AccessTokenIssuer,
    source_tokens: SourceTokenCodec,
    max_attempts: int,
    window_seconds: int,
    session_max_days: int,
    refresh_ttl_days: int,
    email: str,
    password: str,
    device_id: uuid.UUID,
    device_label: str | None,
    platform: str,
    now: datetime | None = None,
) -> IssuedSession:
    """Validate credentials and issue access, refresh and source credentials."""
    moment = now or utcnow()
    normalized = normalize_email(email)
    throttle_key = sha256_digest(normalized)
    if await throttles.locked(throttle_key, moment):
        raise locked_out()
    user = await accounts.by_email(normalized)
    if user is None:
        await hasher.dummy_verify(password)
        await throttles.record_failure(throttle_key, moment, window_seconds, max_attempts)
        raise invalid_credentials()
    if user.password_hash is None:
        await hasher.dummy_verify(password)
        await throttles.record_failure(throttle_key, moment, window_seconds, max_attempts)
        raise invalid_credentials()
    verification = await hasher.verify(password, user.password_hash)
    if not verification.valid:
        await throttles.record_failure(throttle_key, moment, window_seconds, max_attempts)
        raise invalid_credentials()
    if verification.needs_rehash:
        await accounts.update_password(user.id, await hasher.hash(password), moment)
    if user.status is not AccountStatus.ACTIVE:
        raise DomainError(ErrorCode.ACCOUNT_DISABLED, 403, "Account is not active")
    if user.email_verified_at is None:
        raise DomainError(
            ErrorCode.EMAIL_NOT_VERIFIED,
            403,
            "Email verification is required",
            details={"can_resend": True},
        )
    issued = await issue_session(
        devices=devices,
        sessions=sessions,
        refresh=refresh,
        notifications=notifications,
        outbox=outbox,
        security=security,
        access_tokens=access_tokens,
        source_tokens=source_tokens,
        session_max_days=session_max_days,
        refresh_ttl_days=refresh_ttl_days,
        user_id=user.id,
        device_id=device_id,
        device_label=device_label,
        platform=platform,
        now=moment,
    )
    await throttles.clear(throttle_key)
    return issued
