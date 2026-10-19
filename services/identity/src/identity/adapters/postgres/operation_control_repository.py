"""Operation control: cancel flags, leases, control checks and expurgo."""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.operation import OperationState
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_operation import OperationReceiptTable
from .tables_session import SessionTable


class PostgresOperationControlRepository:
    """Control-plane reads/writes separated from receipt creation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def request_cancel(
        self, operation_id: uuid.UUID, user_id: uuid.UUID, now: datetime
    ) -> None:
        """Mark cancel_requested without claiming the provider stopped."""
        await self._session.execute(
            update(OperationReceiptTable)
            .where(
                OperationReceiptTable.id == operation_id,
                OperationReceiptTable.user_id == user_id,
                OperationReceiptTable.state.in_(
                    [OperationState.ACCEPTED.value, OperationState.RUNNING.value]
                ),
            )
            .values(
                cancel_requested=True, state=OperationState.CANCEL_REQUESTED.value, updated_at=now
            )
        )

    async def renew_lease(
        self, operation_id: uuid.UUID, owner: str, now: datetime, expires_at: datetime
    ) -> None:
        """Heartbeat an active receipt."""
        await self._session.execute(
            update(OperationReceiptTable)
            .where(
                OperationReceiptTable.id == operation_id,
                OperationReceiptTable.state.in_(
                    [OperationState.ACCEPTED.value, OperationState.RUNNING.value]
                ),
            )
            .values(lease_owner=owner, lease_expires_at=expires_at, updated_at=now)
        )

    async def recover_expired_leases(self, now: datetime) -> int:
        """Mark receipts whose worker died as interrupted."""
        result = await self._session.execute(
            update(OperationReceiptTable)
            .where(
                OperationReceiptTable.state.in_(
                    [OperationState.ACCEPTED.value, OperationState.RUNNING.value]
                ),
                OperationReceiptTable.lease_expires_at.is_not(None),
                OperationReceiptTable.lease_expires_at < now,
            )
            .values(
                state=OperationState.INTERRUPTED.value,
                finished_at=now,
                updated_at=now,
                error_code="lease_expired",
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def control(
        self, operation_id: uuid.UUID, user_id: uuid.UUID, now: datetime
    ) -> tuple[OperationState, bool, bool] | None:
        """Return state, cancel flag and whether the session is still active."""

        row = await self._session.execute(
            select(
                OperationReceiptTable.state,
                OperationReceiptTable.cancel_requested,
                SessionTable.revoked_at,
                SessionTable.expires_at,
            )
            .join(SessionTable, SessionTable.id == OperationReceiptTable.session_id)
            .where(
                OperationReceiptTable.id == operation_id,
                OperationReceiptTable.user_id == user_id,
            )
        )
        first = row.first()
        if first is None:
            return None
        session_active = first.revoked_at is None and first.expires_at > now
        return OperationState(first.state), bool(first.cancel_requested), session_active

    async def expire_old(self, before: datetime) -> int:
        """Delete receipts past retention."""

        result = await self._session.execute(
            delete(OperationReceiptTable).where(OperationReceiptTable.created_at < before)
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def active_for_session(self, session_id: uuid.UUID) -> bool:
        """Whether any non-terminal operation still belongs to a session."""
        value = await self._session.scalar(
            select(OperationReceiptTable.id)
            .where(
                OperationReceiptTable.session_id == session_id,
                OperationReceiptTable.state.in_(
                    [
                        OperationState.ACCEPTED.value,
                        OperationState.RUNNING.value,
                        OperationState.CANCEL_REQUESTED.value,
                    ]
                ),
            )
            .limit(1)
        )
        return value is not None
