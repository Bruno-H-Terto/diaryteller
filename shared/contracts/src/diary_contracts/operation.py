"""Operation receipts, idempotency and quota reservation contracts.

Receipts contain metadata only. They never contain prompts, transcripts,
answers or any other diary content.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .authorization import UsageMetric


class OperationType(StrEnum):
    """Operations that may consume external provider capacity."""

    AI_RESPONSE = "ai_response"


class OperationState(StrEnum):
    """Minimum lifecycle shared by every billable operation."""

    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


TERMINAL_STATES = frozenset(
    {
        OperationState.SUCCEEDED,
        OperationState.FAILED,
        OperationState.CANCELLED,
        OperationState.INTERRUPTED,
    }
)


class ReserveRequest(BaseModel):
    """Internal request to create a receipt and reserve quota atomically."""

    model_config = ConfigDict(extra="forbid")

    operation_type: OperationType
    permission: str
    idempotency_key: str = Field(min_length=8, max_length=128)
    payload_digest: str = Field(min_length=16, max_length=128)
    metric: UsageMetric
    estimated_amount: int = Field(ge=0)


class ReserveResult(BaseModel):
    """Result of reservation; `created=false` means the key already existed."""

    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    state: OperationState
    created: bool
    result_available: bool = False
    actual_amount: int | None = None


class FinishRequest(BaseModel):
    """Finalize a receipt with known or unknown external consumption."""

    model_config = ConfigDict(extra="forbid")

    state: OperationState
    actual_amount: int | None = Field(default=None, ge=0)
    error_code: str | None = Field(default=None, max_length=64)


class OperationView(BaseModel):
    """Safe metadata returned to the owner."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: OperationType
    state: OperationState
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    updated_at: datetime
    error_code: str | None
    result_available: bool = False


class OperationControl(BaseModel):
    """Control state checked during long streams."""

    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    state: OperationState
    cancel_requested: bool
    session_active: bool
    checked_at: datetime


class ConsumeRequest(BaseModel):
    """Internal request for incremental metered usage (e.g. one MCP call)."""

    model_config = ConfigDict(extra="forbid")

    metric: UsageMetric
    amount: int = Field(ge=1, le=100)
