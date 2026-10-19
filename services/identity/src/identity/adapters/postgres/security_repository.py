"""Minimal security event persistence (administrative metadata only)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .tables_identity import SecurityEventTable


class PostgresSecurityRepository:
    """Append-only security audit."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        user_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        event_type: str,
        reference: str | None,
        now: datetime,
    ) -> None:
        """Store a minimal event without IP, location or diary content."""
        self._session.add(
            SecurityEventTable(
                id=uuid.uuid4(),
                user_id=user_id,
                session_id=session_id,
                event_type=event_type[:48],
                reference=(reference or None) and reference[:120],
                created_at=now,
            )
        )
        await self._session.flush()
