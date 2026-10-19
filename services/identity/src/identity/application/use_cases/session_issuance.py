"""Single place that mints device sessions for every authentication method."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from diary_contracts.errors import DomainError, ErrorCode

from identity.adapters.security.access_tokens import AccessTokenIssuer
from identity.adapters.security.refresh_tokens import new_refresh_token
from identity.adapters.security.source_tokens import SourceTokenCodec
from identity.application.ports.accounts import DeviceConflict, DeviceRepository
from identity.application.ports.notifications import (
    NotificationRepository,
    OutboxRepository,
    SecurityRepository,
)
from identity.application.ports.sessions import RefreshRepository, SessionRepository
from identity.domain.session import RefreshCredential, Session

from .common import IssuedSession


async def issue_session(
    *,
    devices: DeviceRepository,
    sessions: SessionRepository,
    refresh: RefreshRepository,
    notifications: NotificationRepository,
    outbox: OutboxRepository,
    security: SecurityRepository,
    access_tokens: AccessTokenIssuer,
    source_tokens: SourceTokenCodec,
    session_max_days: int,
    refresh_ttl_days: int,
    user_id: uuid.UUID,
    device_id: uuid.UUID,
    device_label: str | None,
    platform: str,
    now: datetime,
) -> IssuedSession:
    """Create a session, rotate the device, and return all credentials."""
    try:
        device = await devices.upsert(user_id, device_id, device_label, platform, now)
    except DeviceConflict as exc:
        raise DomainError(ErrorCode.FORBIDDEN, 403, "Device identifier is not available") from exc
    await sessions.revoke_for_device(user_id, device.id, "replaced_by_login", now)
    session = Session(
        id=uuid.uuid4(),
        user_id=user_id,
        device_id=device.id,
        created_at=now,
        expires_at=now + timedelta(days=session_max_days),
        last_seen_at=now,
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
        issued_at=now,
        expires_at=min(session.expires_at, now + timedelta(days=refresh_ttl_days)),
        consumed_at=None,
        replacement_id=None,
    )
    await refresh.create(credential)
    notification_id = await notifications.create(
        user_id,
        kind="session.new",
        title="Novo acesso",
        body="Uma nova sessão foi iniciada. Se não foi você, revogue-a no aplicativo.",
        now=now,
    )
    await outbox.append(
        "session.new",
        {
            "user_id": str(user_id),
            "session_id": str(session.id),
            "device_id": str(device.id),
            "device_label": device.label or "dispositivo",
            "platform": platform,
            "notification_id": str(notification_id),
        },
        available_at=now,
        dedupe_key=f"session:{session.id}",
    )
    await security.record(
        user_id=user_id,
        session_id=session.id,
        event_type="session.created",
        reference=platform,
        now=now,
    )
    return IssuedSession(
        access_token=access_tokens.issue(user_id, session.id, now),
        refresh_token=token,
        source=source_tokens.issue(session.id, device.id, session.source_version, now),
        session_id=session.id,
    )


@dataclass(frozen=True, slots=True)
class SessionIssuer:
    """Bundle of collaborators so callers can mint a session with one call."""

    devices: DeviceRepository
    sessions: SessionRepository
    refresh: RefreshRepository
    notifications: NotificationRepository
    outbox: OutboxRepository
    security: SecurityRepository
    access_tokens: AccessTokenIssuer
    source_tokens: SourceTokenCodec
    session_max_days: int
    refresh_ttl_days: int

    async def issue(
        self,
        *,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        device_label: str | None,
        platform: str,
        now: datetime,
    ) -> IssuedSession:
        """Issue credentials through the shared session pipeline."""
        return await issue_session(
            devices=self.devices,
            sessions=self.sessions,
            refresh=self.refresh,
            notifications=self.notifications,
            outbox=self.outbox,
            security=self.security,
            access_tokens=self.access_tokens,
            source_tokens=self.source_tokens,
            session_max_days=self.session_max_days,
            refresh_ttl_days=self.refresh_ttl_days,
            user_id=user_id,
            device_id=device_id,
            device_label=device_label,
            platform=platform,
            now=now,
        )
