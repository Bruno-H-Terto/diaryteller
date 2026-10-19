"""Account self-service use cases: profile, sessions, push and notifications."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from diary_contracts.errors import DomainError, ErrorCode
from diary_security import encrypt_json

from identity.application.ports.accounts import AccountRepository, DeviceRepository
from identity.application.ports.notifications import (
    NotificationRepository,
    PushTokenRepository,
    SecurityRepository,
)
from identity.application.ports.sessions import SessionRepository
from identity.domain.session import Session

from .common import utcnow


def session_view(session: Session, current_session_id: uuid.UUID) -> dict[str, Any]:
    """Represent one session without tokens or device-identifying secrets."""
    return {
        "id": session.id,
        "device_id": session.device_id,
        "created_at": session.created_at,
        "expires_at": session.expires_at,
        "last_seen_at": session.last_seen_at,
        "revoked_at": session.revoked_at,
        "revocation_reason": session.revocation_reason,
        "is_current": session.id == current_session_id,
        "is_active": session.is_active(),
    }


async def list_sessions(
    *, sessions: SessionRepository, user_id: uuid.UUID, current_session_id: uuid.UUID
) -> list[dict[str, Any]]:
    """List the caller's sessions, marking the current one."""
    return [
        session_view(session, current_session_id)
        for session in await sessions.list_for_user(user_id)
    ]


async def revoke_owned_session(
    *,
    sessions: SessionRepository,
    security: SecurityRepository,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    """Revoke a session only when it belongs to the caller."""
    moment = now or utcnow()
    target = await sessions.by_id(session_id)
    if target is None or target.user_id != user_id:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Session not found")
    await sessions.revoke(session_id, "user_revoked", moment)
    await security.record(
        user_id=user_id,
        session_id=session_id,
        event_type="session.revoked",
        reference="user",
        now=moment,
    )


async def revoke_other_sessions(
    *,
    sessions: SessionRepository,
    security: SecurityRepository,
    user_id: uuid.UUID,
    current_session_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    """Revoke all sessions except the current one."""
    moment = now or utcnow()
    await sessions.revoke_others(user_id, current_session_id, "user_revoked_others", moment)
    await security.record(
        user_id=user_id,
        session_id=current_session_id,
        event_type="sessions.revoked_others",
        reference=None,
        now=moment,
    )


async def put_push_token(
    *,
    devices: DeviceRepository,
    push_repository: PushTokenRepository,
    push_key: str,
    user_id: uuid.UUID,
    device_id: uuid.UUID,
    token: str,
    platform: str,
    now: datetime | None = None,
) -> None:
    """Store an encrypted push token for an owned device."""
    if platform not in {"android", "ios"}:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Unsupported platform")
    if await devices.get(user_id, device_id) is None:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Device not found")
    moment = now or utcnow()
    ciphertext = encrypt_json({"token": token, "platform": platform}, push_key)
    await push_repository.upsert(user_id, device_id, ciphertext, platform, moment)


async def delete_push_token(
    *, push_repository: PushTokenRepository, user_id: uuid.UUID, device_id: uuid.UUID
) -> None:
    """Remove a registration idempotently."""
    await push_repository.delete(user_id, device_id)


async def list_notifications(
    *,
    notifications: NotificationRepository,
    user_id: uuid.UUID,
    limit: int,
    before: datetime | None,
) -> list[dict[str, Any]]:
    """List own administrative notifications."""
    return await notifications.list_for_user(user_id, limit=limit, before=before)


async def mark_notification_read(
    *,
    notifications: NotificationRepository,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    """Mark own notification read."""
    if not await notifications.mark_read(user_id, notification_id, now or utcnow()):
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Notification not found")


async def request_account_deletion(
    *,
    accounts: AccountRepository,
    sessions: SessionRepository,
    security: SecurityRepository,
    user_id: uuid.UUID,
    authenticated_at: datetime,
    grace_days: int,
    now: datetime | None = None,
) -> None:
    """Require recent authentication, revoke sessions and schedule purge."""
    moment = now or utcnow()
    if moment - authenticated_at > timedelta(minutes=5):
        raise DomainError(
            ErrorCode.RECENT_AUTH_REQUIRED,
            403,
            "Recent authentication is required",
        )
    await sessions.revoke_all(user_id, "account_deletion", moment)
    await accounts.schedule_deletion(user_id, moment, moment + timedelta(days=grace_days))
    await security.record(
        user_id=user_id,
        session_id=None,
        event_type="account.deletion_requested",
        reference=None,
        now=moment,
    )


async def update_profile(
    *,
    accounts: AccountRepository,
    user_id: uuid.UUID,
    display_name: str | None,
    locale: str | None,
    timezone: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Update only explicitly editable profile fields."""
    profile = await accounts.update_profile(
        user_id,
        display_name=display_name,
        locale=locale,
        timezone=timezone,
        now=now or utcnow(),
    )
    return {
        "id": profile.id,
        "display_name": profile.display_name,
        "locale": profile.locale,
        "timezone": profile.timezone,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
