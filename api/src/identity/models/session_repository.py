"""PostgreSQL sessions and rotating refresh credentials."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.session import RefreshCredential, Session

from .tables_session import RefreshCredentialTable, SessionTable


def _session(row: SessionTable) -> Session:
    return Session(
        id=row.id,
        user_id=row.user_id,
        device_id=row.device_id,
        created_at=row.created_at,
        expires_at=row.expires_at,
        last_seen_at=row.last_seen_at,
        revoked_at=row.revoked_at,
        revocation_reason=row.revocation_reason,
        source_version=row.source_version,
    )


def _credential(row: RefreshCredentialTable) -> RefreshCredential:
    return RefreshCredential(
        id=row.id,
        session_id=row.session_id,
        family_id=row.family_id,
        digest=row.digest,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        consumed_at=row.consumed_at,
        replacement_id=row.replacement_id,
    )


class PostgresSessionRepository:
    """Session persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_id(self, session_id: uuid.UUID) -> Session | None:
        """Load by primary key."""
        row = await self._session.get(SessionTable, session_id)
        return _session(row) if row else None

    async def create(self, value: Session) -> None:
        """Insert a session."""
        self._session.add(
            SessionTable(
                id=value.id,
                user_id=value.user_id,
                device_id=value.device_id,
                created_at=value.created_at,
                expires_at=value.expires_at,
                last_seen_at=value.last_seen_at,
                revoked_at=value.revoked_at,
                revocation_reason=value.revocation_reason,
                source_version=value.source_version,
            )
        )
        await self._session.flush()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Session]:
        """List user sessions."""
        rows = await self._session.scalars(
            select(SessionTable)
            .where(SessionTable.user_id == user_id)
            .order_by(SessionTable.created_at.desc())
        )
        return [_session(row) for row in rows]

    async def revoke(
        self,
        session_id: uuid.UUID,
        reason: str,
        now: datetime,
        *,
        bump_source_version: bool = True,
    ) -> None:
        """Revoke one session, optionally invalidating its source token."""
        values: dict[str, object] = {
            "revoked_at": func.coalesce(SessionTable.revoked_at, now),
            "revocation_reason": reason[:64],
        }
        if bump_source_version:
            values["source_version"] = SessionTable.source_version + 1
        await self._session.execute(
            update(SessionTable).where(SessionTable.id == session_id).values(**values)
        )

    async def revoke_others(
        self, user_id: uuid.UUID, keep_session_id: uuid.UUID, reason: str, now: datetime
    ) -> int:
        """Revoke every other session of the user."""
        result = await self._session.execute(
            update(SessionTable)
            .where(
                SessionTable.user_id == user_id,
                SessionTable.id != keep_session_id,
                SessionTable.revoked_at.is_(None),
            )
            .values(
                revoked_at=now,
                revocation_reason=reason[:64],
                source_version=SessionTable.source_version + 1,
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def revoke_all(self, user_id: uuid.UUID, reason: str, now: datetime) -> int:
        """Revoke every active session of the user."""
        result = await self._session.execute(
            update(SessionTable)
            .where(SessionTable.user_id == user_id, SessionTable.revoked_at.is_(None))
            .values(
                revoked_at=now,
                revocation_reason=reason[:64],
                source_version=SessionTable.source_version + 1,
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def revoke_for_device(
        self, user_id: uuid.UUID, device_id: uuid.UUID, reason: str, now: datetime
    ) -> int:
        """Revoke active sessions for one device."""
        result = await self._session.execute(
            update(SessionTable)
            .where(
                SessionTable.user_id == user_id,
                SessionTable.device_id == device_id,
                SessionTable.revoked_at.is_(None),
            )
            .values(
                revoked_at=now,
                revocation_reason=reason[:64],
                source_version=SessionTable.source_version + 1,
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def touch(self, session_id: uuid.UUID, now: datetime) -> None:
        """Update last seen."""
        await self._session.execute(
            update(SessionTable).where(SessionTable.id == session_id).values(last_seen_at=now)
        )

    async def bump_source_version(self, session_id: uuid.UUID) -> int:
        """Increment the source version and return the new value."""
        value = await self._session.scalar(
            update(SessionTable)
            .where(SessionTable.id == session_id)
            .values(source_version=SessionTable.source_version + 1)
            .returning(SessionTable.source_version)
        )
        await self._session.flush()
        return int(value or 0)

    async def active_count(self, user_id: uuid.UUID) -> int:
        """Count active sessions."""
        value = await self._session.scalar(
            select(func.count())
            .select_from(SessionTable)
            .where(
                SessionTable.user_id == user_id,
                SessionTable.revoked_at.is_(None),
                SessionTable.expires_at > func.now(),
            )
        )
        return int(value or 0)
