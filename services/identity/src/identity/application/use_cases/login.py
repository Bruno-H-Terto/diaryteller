"""Authenticate a device and create a persisted, revocable session.

The notification content is generic and contains no diary data. The refresh
credential is stored as a digest only.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from diary_contracts.authorization import AccountStatus
from diary_contracts.errors import DomainError, ErrorCode
from diary_security import sha256_digest

from identity.adapters.security.access_tokens import AccessTokenIssuer
from identity.adapters.security.passwords import PasswordHasher
from identity.adapters.security.refresh_tokens import new_refresh_token
from identity.adapters.security.source_tokens import SourceTokenCodec
from identity.application.ports.accounts import (
    AccountRepository,
    DeviceConflict,
    DeviceRepository,
    ThrottleRepository,
)
from identity.application.ports.notifications import (
    NotificationRepository,
    OutboxRepository,
    SecurityRepository,
)
from identity.application.ports.sessions import RefreshRepository, SessionRepository
from identity.domain.session import RefreshCredential, Session

from .common import IssuedSession, invalid_credentials, locked_out, normalize_email, utcnow


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
    try:
        device = await devices.upsert(user.id, device_id, device_label, platform, moment)
    except DeviceConflict as exc:
        raise DomainError(ErrorCode.FORBIDDEN, 403, "Device identifier is not available") from exc
    await sessions.revoke_for_device(user.id, device.id, "replaced_by_login", moment)
    session = Session(
        id=uuid.uuid4(),
        user_id=user.id,
        device_id=device.id,
        created_at=moment,
        expires_at=moment + timedelta(days=session_max_days),
        last_seen_at=moment,
        revoked_at=None,
        revocation_reason=None,
        source_version=1,
    )
    await sessions.create(session)
    token, digest = new_refresh_token()
    credential = RefreshCredential(
        id=uuid.uuid4(),
        session_id=session.id,
        family_id=uuid.uuid4(),
        digest=digest,
        issued_at=moment,
        expires_at=min(
            session.expires_at,
            moment + timedelta(days=refresh_ttl_days),
        ),
        consumed_at=None,
        replacement_id=None,
    )
    await refresh.create(credential)
    notification_id = await notifications.create(
        user.id,
        kind="session.new",
        title="Novo acesso",
        body="Uma nova sessão foi iniciada. Se não foi você, revogue-a no aplicativo.",
        now=moment,
    )
    await outbox.append(
        "session.new",
        {
            "user_id": str(user.id),
            "session_id": str(session.id),
            "device_id": str(device.id),
            "device_label": device.label or "dispositivo",
            "platform": platform,
            "notification_id": str(notification_id),
        },
        available_at=moment,
        dedupe_key=f"session:{session.id}",
    )
    await throttles.clear(throttle_key)
    await security.record(
        user_id=user.id,
        session_id=session.id,
        event_type="session.created",
        reference=platform,
        now=moment,
    )
    return IssuedSession(
        access_token=access_tokens.issue(user.id, session.id, moment),
        refresh_token=token,
        source=source_tokens.issue(session.id, device.id, session.source_version, moment),
        session_id=session.id,
    )
