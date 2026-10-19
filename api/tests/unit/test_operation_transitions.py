"""Operation state machine tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from diary_contracts.authorization import UsageMetric
from diary_contracts.operation import OperationState, OperationType
from identity.models.operation import InvalidTransition, OperationReceipt


def receipt(state: OperationState = OperationState.ACCEPTED) -> OperationReceipt:
    now = datetime(2026, 10, 19, tzinfo=UTC)
    return OperationReceipt(
        id=uuid4(),
        user_id=uuid4(),
        session_id=uuid4(),
        operation_type=OperationType.AI_RESPONSE,
        permission="conversation:use",
        idempotency_key="key-12345678",
        payload_digest="a" * 32,
        metric=UsageMetric.AI_TOKENS,
        reserved_amount=100,
        actual_amount=None,
        state=state,
        error_code=None,
        created_at=now,
        started_at=None,
        finished_at=None,
        updated_at=now,
        lease_owner=None,
        lease_expires_at=None,
    )


def test_running_sets_started_at() -> None:
    value = receipt().transition(OperationState.RUNNING)
    assert value.started_at is not None
    assert value.finished_at is None


def test_success_is_terminal() -> None:
    value = receipt(OperationState.RUNNING).transition(OperationState.SUCCEEDED)
    with pytest.raises(InvalidTransition):
        value.transition(OperationState.RUNNING)


def test_cancel_requested_can_finish_cancelled() -> None:
    value = receipt(OperationState.RUNNING).transition(OperationState.CANCEL_REQUESTED)
    assert value.finish(OperationState.CANCELLED).state is OperationState.CANCELLED


def test_cannot_cancel_after_success() -> None:
    value = receipt(OperationState.RUNNING).transition(OperationState.SUCCEEDED)
    with pytest.raises(InvalidTransition):
        value.finish(OperationState.CANCELLED)
