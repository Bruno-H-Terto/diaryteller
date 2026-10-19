"""Contract validation tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from diary_contracts.context import ContextBundle, ContextRecord
from diary_contracts.conversation import ConversationRequest, FinalResult
from diary_contracts.stream import StreamEvent, StreamEventType, encode_sse
from diary_contracts.suggestions import GoalProposal, ReminderProposal
from pydantic import ValidationError


def record(identifier: str = "r1", event_at: datetime | None = None) -> ContextRecord:
    return ContextRecord(
        id=identifier,
        recorded_at=datetime(2026, 10, 18, 20, tzinfo=UTC),
        event_at=event_at,
        text="texto sintético",
    )


def test_context_requires_unique_ids() -> None:
    with pytest.raises(ValidationError):
        ContextBundle(records=[record(), record()])


def test_context_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        ContextRecord(id="r1", recorded_at=datetime(2026, 1, 1), text="x")


def test_memory_mode_requires_context() -> None:
    with pytest.raises(ValidationError):
        ConversationRequest(
            client_message_id=uuid4(),
            conversation_id="c1",
            mode="timeline",  # type: ignore[arg-type]
            message="x",
        )


def test_proposals_require_confirmation() -> None:
    with pytest.raises(ValidationError):
        GoalProposal(  # type: ignore[arg-type]
            id=uuid4(), text="goal", source_ids=[], requires_confirmation=False  # type: ignore[arg-type]
        )


def test_reminder_keeps_timezone() -> None:
    reminder = ReminderProposal(
        id=uuid4(), text="ligar", source_ids=["r1"], timezone="America/Sao_Paulo"
    )
    assert reminder.requires_confirmation is True


def test_final_result_limits_follow_ups() -> None:
    with pytest.raises(ValidationError):
        FinalResult(
            operation_id=uuid4(),
            answer="ok",
            follow_up_questions=["1", "2", "3"],
        )


def test_sse_event_has_sequence_and_operation() -> None:
    operation = uuid4()
    frame = encode_sse(
        StreamEvent(
            operation_id=operation,
            sequence=7,
            type=StreamEventType.TEXT_DELTA,
            data={"text": "olá"},
        )
    )
    assert frame.startswith("event: text_delta")
    body = json.loads(frame.split("data: ", 1)[1].split("\n", 1)[0])
    assert body == {"operation_id": str(operation), "sequence": 7, "text": "olá"}
