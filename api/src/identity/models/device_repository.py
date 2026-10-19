"""Device persistence owned by the account module."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.profile import Device

from .errors import DeviceConflict
from .tables_identity import DeviceTable


class PostgresDeviceRepository:
    """Device upsert/touch."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        label: str | None,
        platform: str,
        now: datetime,
    ) -> Device:
        """Create or refresh a user-owned device."""
        row = await self._session.get(DeviceTable, device_id)
        if row is not None and row.user_id != user_id:
            raise DeviceConflict("device id belongs to another account")
        if row is None:
            row = DeviceTable(
                id=device_id,
                user_id=user_id,
                label=label,
                platform=platform,
                created_at=now,
                last_seen_at=now,
            )
            self._session.add(row)
        else:
            row.label = label or row.label
            row.platform = platform
            row.last_seen_at = now
        await self._session.flush()
        return Device(
            id=row.id,
            user_id=row.user_id,
            label=row.label,
            platform=row.platform,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
        )

    async def get(self, user_id: uuid.UUID, device_id: uuid.UUID) -> Device | None:
        """Load an owned device."""
        row = await self._session.scalar(
            select(DeviceTable).where(DeviceTable.id == device_id, DeviceTable.user_id == user_id)
        )
        if row is None:
            return None
        return Device(
            id=row.id,
            user_id=row.user_id,
            label=row.label,
            platform=row.platform,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
        )

    async def touch(self, user_id: uuid.UUID, device_id: uuid.UUID, now: datetime) -> None:
        """Best-effort last seen update."""
        await self._session.execute(
            update(DeviceTable)
            .where(DeviceTable.id == device_id, DeviceTable.user_id == user_id)
            .values(last_seen_at=now)
        )
