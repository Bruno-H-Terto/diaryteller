"""Operation receipt and control persistence ports."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from diary_contracts.authorization import UsageMetric
from diary_contracts.operation import OperationState, OperationType

from identity.domain.operation import OperationReceipt


class OperationRepository(Protocol):
    """Receipt creation and state transitions."""

    async def create_or_get(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        operation_type: OperationType,
        permission: str,
        idempotency_key: str,
        payload_digest: str,
        metric: UsageMetric,
        reserved_amount: int,
        now: datetime,
    ) -> tuple[OperationReceipt, bool]:
        """Insert or return existing receipt."""
        ...

    async def by_id(self, operation_id: UUID, user_id: UUID) -> OperationReceipt | None:
        """Owner-scoped read."""
        ...

    async def lock(self, operation_id: UUID, user_id: UUID) -> OperationReceipt | None:
        """Lock for transition."""
        ...

    async def apply(self, receipt: OperationReceipt, now: datetime) -> None:
        """Persist a validated transition."""
        ...


class OperationControlRepository(Protocol):
    """Cancel, lease and control checks."""

    async def request_cancel(self, operation_id: UUID, user_id: UUID, now: datetime) -> None:
        """Set cancel_requested."""
        ...

    async def renew_lease(
        self, operation_id: UUID, owner: str, now: datetime, expires_at: datetime
    ) -> None:
        """Heartbeat a lease."""
        ...

    async def control(
        self, operation_id: UUID, user_id: UUID, now: datetime
    ) -> tuple[OperationState, bool, bool] | None:
        """Return state, cancel flag and session activity."""
        ...

    async def recover_expired_leases(self, now: datetime) -> int:
        """Mark dead workers' receipts interrupted."""
        ...

    async def expire_old(self, before: datetime) -> int:
        """Delete receipts past retention."""
        ...

    async def active_for_session(self, session_id: UUID) -> bool:
        """Whether a session has a non-terminal operation."""
        ...
