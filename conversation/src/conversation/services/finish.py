"""Operation finalization helpers, including disconnect best effort."""

from __future__ import annotations

import asyncio
import logging

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import FinishRequest, OperationState

from conversation.lib.ports import IdentityPort
from conversation.models.evidence import EvidenceError
from conversation.services.prepare import PreparedOperation
from conversation.services.stream_events import OperationCancelled, ProviderTimeout

_logger = logging.getLogger(__name__)


def classify(exc: Exception) -> tuple[OperationState, str, bool]:
    """Map an application failure to a terminal state and safe code."""
    if isinstance(exc, OperationCancelled):
        return OperationState.CANCELLED, ErrorCode.OPERATION_CANCELLED.value, False
    if isinstance(exc, ProviderTimeout):
        return OperationState.FAILED, ErrorCode.PROVIDER_TIMEOUT.value, True
    if isinstance(exc, EvidenceError):
        return OperationState.FAILED, ErrorCode.PROVIDER_UNAVAILABLE.value, True
    if isinstance(exc, DomainError):
        return OperationState.FAILED, exc.code.value, exc.retryable
    return OperationState.FAILED, ErrorCode.INTERNAL_ERROR.value, True


def safe_message(exc: Exception) -> str:
    """Return a user-safe message without provider payloads."""
    if isinstance(exc, OperationCancelled):
        return "Operation cancelled"
    if isinstance(exc, ProviderTimeout):
        return "AI provider timed out"
    if isinstance(exc, EvidenceError):
        return "AI provider returned an invalid result"
    if isinstance(exc, DomainError):
        return exc.title
    return "Response failed"


async def finish(
    identity: IdentityPort,
    prepared: PreparedOperation,
    state: OperationState,
    actual: int | None,
    error_code: str | None,
) -> None:
    """Call the idempotent finish callback."""
    await identity.finish(
        prepared.auth,
        prepared.operation_id,
        FinishRequest(state=state, actual_amount=actual, error_code=error_code),
    )


def best_effort_finish(
    identity: IdentityPort,
    prepared: PreparedOperation,
    state: OperationState,
    actual: int | None,
    error_code: str | None,
) -> None:
    """Schedule finalization that must outlive a cancelled generator."""

    async def run() -> None:
        try:
            await finish(identity, prepared, state, actual, error_code)
        except Exception:
            _logger.warning(
                "finish_failed",
                extra={
                    "operation_id": str(prepared.operation_id),
                    "error_code": "finish_failed",
                },
            )

    task = asyncio.create_task(run())
    task.add_done_callback(lambda value: value.exception() if value.done() else None)
