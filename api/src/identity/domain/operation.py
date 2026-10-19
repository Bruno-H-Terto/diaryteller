"""Operation receipt state machine and lease metadata.

Transitions are validated in the domain and applied atomically by SQL. Receipts
never carry AI answers, prompts, transcripts or media.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from diary_contracts.authorization import UsageMetric
from diary_contracts.operation import OperationState, OperationType

from .session import utcnow

_ALLOWED: dict[OperationState, frozenset[OperationState]] = {
    OperationState.ACCEPTED: frozenset(
        {
            OperationState.RUNNING,
            OperationState.FAILED,
            OperationState.CANCEL_REQUESTED,
            OperationState.CANCELLED,
            OperationState.INTERRUPTED,
        }
    ),
    OperationState.RUNNING: frozenset(
        {
            OperationState.SUCCEEDED,
            OperationState.FAILED,
            OperationState.CANCEL_REQUESTED,
            OperationState.CANCELLED,
            OperationState.INTERRUPTED,
        }
    ),
    OperationState.CANCEL_REQUESTED: frozenset(
        {
            OperationState.CANCELLED,
            OperationState.FAILED,
            OperationState.INTERRUPTED,
        }
    ),
    OperationState.SUCCEEDED: frozenset(),
    OperationState.FAILED: frozenset(),
    OperationState.CANCELLED: frozenset(),
    OperationState.INTERRUPTED: frozenset(),
}


class InvalidTransition(ValueError):
    """Raised when a caller tries to move a terminal receipt backwards."""


@dataclass(frozen=True, slots=True)
class OperationReceipt:
    """Metadata for one idempotent, billable operation."""

    id: UUID
    user_id: UUID
    session_id: UUID
    operation_type: OperationType
    permission: str
    idempotency_key: str
    payload_digest: str
    metric: UsageMetric
    reserved_amount: int
    actual_amount: int | None
    state: OperationState
    error_code: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    updated_at: datetime
    lease_owner: str | None
    lease_expires_at: datetime | None

    def transition(self, target: OperationState, now: datetime | None = None) -> OperationReceipt:
        """Return a copy in `target` or raise when the transition is invalid."""
        if target is self.state:
            return self
        if target not in _ALLOWED[self.state]:
            raise InvalidTransition(f"cannot transition {self.state} to {target}")
        moment = now or utcnow()
        started = self.started_at
        if target is OperationState.RUNNING and started is None:
            started = moment
        finished = self.finished_at
        if target in {
            OperationState.SUCCEEDED,
            OperationState.FAILED,
            OperationState.CANCELLED,
            OperationState.INTERRUPTED,
        }:
            finished = moment
        return replace(
            self,
            state=target,
            updated_at=moment,
            started_at=started,
            finished_at=finished,
        )

    def finish(
        self,
        target: OperationState,
        *,
        actual_amount: int | None = None,
        error_code: str | None = None,
        now: datetime | None = None,
    ) -> OperationReceipt:
        """Apply a terminal transition and known/unknown consumption."""
        updated = self.transition(target, now)
        return replace(
            updated,
            actual_amount=actual_amount,
            error_code=(error_code or updated.error_code or "")[:64] or None,
        )
