"""Push token persistence; tokens are encrypted before reaching this layer."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_identity import PushTokenTable


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

    async def recipients(
        self, user_id: uuid.UUID, exclude_device_id: uuid.UUID | None = None
    ) -> list[dict[str, str]]:
        """Return encrypted push tokens, optionally skipping one device."""
        query = select(PushTokenTable).where(PushTokenTable.user_id == user_id)
        if exclude_device_id is not None:
            query = query.where(PushTokenTable.device_id != exclude_device_id)
        rows = await self._session.scalars(query)
        return [
            {"device_id": str(row.device_id), "token_ciphertext": row.token_ciphertext}
            for row in rows
        ]

    async def delete(self, user_id: uuid.UUID, device_id: uuid.UUID) -> None:
        """Remove a registration owned by the user."""
        await self._session.execute(
            delete(PushTokenTable).where(
                PushTokenTable.user_id == user_id,
                PushTokenTable.device_id == device_id,
            )
        )
