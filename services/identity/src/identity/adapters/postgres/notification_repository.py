"""Notifications, verification tokens and push registrations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_identity import (
    NotificationTable,
    PushTokenTable,
    VerificationTokenTable,
)


class PostgresNotificationRepository:
    """Administrative notifications owned by one user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        *,
        kind: str,
        title: str,
        body: str,
        now: datetime,
    ) -> uuid.UUID:
        """Create a notification with non-diary text."""
        notification_id = uuid.uuid4()
        self._session.add(
            NotificationTable(
                id=notification_id,
                user_id=user_id,
                kind=kind[:40],
                title=title[:160],
                body=body[:500],
                created_at=now,
            )
        )
        await self._session.flush()
        return notification_id

    async def list_for_user(
        self, user_id: uuid.UUID, *, limit: int, before: datetime | None
    ) -> list[dict[str, Any]]:
        """Newest-first cursor list."""
        stmt = select(NotificationTable).where(NotificationTable.user_id == user_id)
        if before is not None:
            stmt = stmt.where(NotificationTable.created_at < before)
        rows = await self._session.scalars(
            stmt.order_by(NotificationTable.created_at.desc()).limit(limit)
        )
        return [
            {
                "id": row.id,
                "kind": row.kind,
                "title": row.title,
                "body": row.body,
                "read": row.read_at is not None,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def mark_read(
        self, user_id: uuid.UUID, notification_id: uuid.UUID, now: datetime
    ) -> bool:
        """Mark an owned notification read."""
        result = await self._session.execute(
            update(NotificationTable)
            .where(
                NotificationTable.id == notification_id,
                NotificationTable.user_id == user_id,
            )
            .values(read_at=now)
        )
        return bool(getattr(result, "rowcount", 0))


class PostgresVerificationRepository:
    """Single-use token digests."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        purpose: str,
        digest: str,
        secret_ciphertext: str,
        expires_at: datetime,
        now: datetime,
    ) -> None:
        """Store digest and encrypted delivery material."""
        self._session.add(
            VerificationTokenTable(
                id=uuid.uuid4(),
                user_id=user_id,
                purpose=purpose,
                digest=digest,
                secret_ciphertext=secret_ciphertext,
                expires_at=expires_at,
                created_at=now,
            )
        )
        await self._session.flush()

    async def consume(self, purpose: str, digest: str, now: datetime) -> uuid.UUID | None:
        """Atomically consume a token and erase its delivery material."""
        row = await self._session.execute(
            update(VerificationTokenTable)
            .where(
                VerificationTokenTable.purpose == purpose,
                VerificationTokenTable.digest == digest,
                VerificationTokenTable.used_at.is_(None),
                VerificationTokenTable.expires_at > now,
            )
            .values(used_at=now, secret_ciphertext="")
            .returning(VerificationTokenTable.user_id)
        )
        first = row.first()
        return first[0] if first else None

    async def invalidate_user(self, user_id: uuid.UUID, purpose: str, now: datetime) -> None:
        """Invalidate outstanding tokens for a purpose."""
        await self._session.execute(
            update(VerificationTokenTable)
            .where(
                VerificationTokenTable.user_id == user_id,
                VerificationTokenTable.purpose == purpose,
                VerificationTokenTable.used_at.is_(None),
            )
            .values(used_at=now)
        )


class PostgresPushRepository:
    """Push registration storage (token encrypted at rest)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        token_ciphertext: str,
        platform: str,
        now: datetime,
    ) -> None:
        """Create or replace the registration for a user device."""
        existing = await self._session.scalar(
            select(PushTokenTable).where(
                PushTokenTable.user_id == user_id,
                PushTokenTable.device_id == device_id,
            )
        )
        if existing is None:
            self._session.add(
                PushTokenTable(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    device_id=device_id,
                    token_ciphertext=token_ciphertext,
                    platform=platform,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            existing.token_ciphertext = token_ciphertext
            existing.platform = platform
            existing.updated_at = now
        await self._session.flush()

    async def delete(self, user_id: uuid.UUID, device_id: uuid.UUID) -> None:
        """Remove a registration owned by the user."""
        await self._session.execute(
            delete(PushTokenTable).where(
                PushTokenTable.user_id == user_id,
                PushTokenTable.device_id == device_id,
            )
        )
