"""Persistence ports for upload quotas."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from diary_contracts.quota import UploadMetric

from identity.adapters.postgres.upload_quota_shared import QuotaState


class UploadQuotaRepository(Protocol):
    """Reservations for metered upload metrics."""

    async def reserve(
        self,
        owner_id: UUID,
        metric: UploadMetric,
        amount: int,
        limit: int,
        reference: str,
        ttl_seconds: int,
        now: datetime,
    ) -> QuotaState:
        """Reserve units or return the live reservation for the reference."""
        ...

    async def commit(self, owner_id: UUID, reservation_id: UUID, now: datetime) -> None:
        """Settle a reservation as consumed."""
        ...

    async def release(self, owner_id: UUID, reservation_id: UUID, now: datetime) -> None:
        """Return reserved units without consuming them."""
        ...


class UploadQuotaGaugeRepository(Protocol):
    """Capacity gauges and quota snapshots."""

    async def acquire(
        self,
        owner_id: UUID,
        metric: UploadMetric,
        amount: int,
        limit: int,
        reference: str,
        now: datetime,
    ) -> QuotaState:
        """Increase a capacity gauge once per reference."""
        ...

    async def close(
        self,
        owner_id: UUID,
        metric: UploadMetric,
        amount: int,
        reference: str,
        now: datetime,
    ) -> None:
        """Decrease a capacity gauge once per reference."""
        ...

    async def expire_stale(self, now: datetime) -> int:
        """Expire reservations past their TTL."""
        ...

    async def reset_owner(self, owner_id: UUID) -> None:
        """Delete all quota state for an account."""
        ...

    async def snapshot(
        self, owner_id: UUID, metrics: list[UploadMetric], now: datetime
    ) -> dict[str, QuotaState]:
        """Load current numbers for several metrics."""
        ...
