"""Diary action validation: what a reply may change on the phone."""

from __future__ import annotations

import json
from uuid import uuid4

from conversation.models.evidence import parse_final_result
from conversation.models.response import MARKER
from diary_contracts.diary import DiarySnapshot
from diary_contracts.diary_actions import CreateEvent


def raw(payload: dict, answer: str = "Resposta") -> str:
    return f"{answer}\n{MARKER}{json.dumps(payload)}"


SNAPSHOT = {
    "entities": [{"id": "a1", "kind": "person", "name": "Ana"}],
    "events": [
        {"id": "e1", "title": "Aniversário", "event_date": "2024-03-01", "precision": "month"}
    ],
    "today": "2026-10-19",
}


def test_actions_are_parsed_and_linked_to_the_snapshot() -> None:
    result = parse_final_result(
        raw(
            {
                "actions": [
                    {
                        "kind": "create_event",
                        "ref": "new:1",
                        "title": "Almoço",
                        "participants": ["a1", "new:2"],
                        "event_date": "2026-10-19",
                        "precision": "day",
                    },
                    {
                        "kind": "create_entity",
                        "ref": "new:2",
                        "entity_kind": "person",
                        "name": "Bruno",
                    },
                ]
            }
        ),
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
        snapshot=DiarySnapshot.model_validate(SNAPSHOT),
    )
    assert [action.kind.value for action in result.actions] == ["create_event", "create_entity"]


def test_action_with_unknown_participant_is_dropped() -> None:
    result = parse_final_result(
        raw(
            {
                "actions": [
                    {
                        "kind": "create_event",
                        "ref": "new:1",
                        "title": "Almoço",
                        "participants": ["inventado"],
                    }
                ]
            }
        ),
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
        snapshot=DiarySnapshot.model_validate(SNAPSHOT),
    )
    assert result.actions == []
    assert result.answer == "Resposta"


def test_undated_event_keeps_unknown_precision() -> None:
    result = parse_final_result(
        raw({"actions": [{"kind": "create_event", "ref": "new:1", "title": "Sem data"}]}),
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
    )
    action = result.actions[0]
    assert isinstance(action, CreateEvent)
    assert action.precision.value == "unknown"
    assert action.event_date is None


def test_invalid_action_keeps_the_answer() -> None:
    result = parse_final_result(
        raw(
            {
                "actions": [
                    {"kind": "create_event", "ref": "new:1", "title": "X", "precision": "day"},
                    {
                        "kind": "create_entity",
                        "ref": "new:2",
                        "entity_kind": "person",
                        "name": "Ana",
                    },
                ]
            }
        ),
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
    )
    assert [action.kind.value for action in result.actions] == ["create_entity"]


def test_link_to_unknown_event_is_dropped() -> None:
    result = parse_final_result(
        raw({"actions": [{"kind": "link_entity", "entity": "a1", "event": "new:9"}]}),
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
        snapshot=DiarySnapshot.model_validate(SNAPSHOT),
    )
    assert result.actions == []


def test_guessed_record_ids_are_dropped_without_losing_the_event() -> None:
    result = parse_final_result(
        raw(
            {
                "actions": [
                    {
                        "kind": "create_event",
                        "ref": "new:1",
                        "title": "Almoço",
                        "source_ids": ["invented"],
                    }
                ]
            }
        ),
        operation_id=uuid4(),
        allowed_ids={"a"},
        timezone="UTC",
    )
    assert isinstance(result.actions[0], CreateEvent)
    assert result.actions[0].source_ids == []


def test_placeholder_date_means_no_date() -> None:
    result = parse_final_result(
        raw(
            {
                "actions": [
                    {
                        "kind": "create_event",
                        "ref": "new:1",
                        "title": "Almoço",
                        "event_date": "unknown",
                        "precision": "unknown",
                    }
                ]
            }
        ),
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
    )
    action = result.actions[0]
    assert isinstance(action, CreateEvent)
    assert action.event_date is None
    assert result.warnings == []
