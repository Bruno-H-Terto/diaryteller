"""Result/evidence validation tests."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from conversation.models.evidence import EvidenceError, parse_final_result
from conversation.models.response import MARKER, MarkerFilter
from diary_contracts.diary import DiarySnapshot
from diary_contracts.diary_actions import CreateEvent


def raw(payload: dict, answer: str = "Resposta") -> str:
    return f"{answer}\n{MARKER}{json.dumps(payload)}"


def test_valid_result_and_sources() -> None:
    result = parse_final_result(
        raw({"source_ids": ["a"], "follow_up_questions": ["q"]}),
        operation_id=uuid4(),
        allowed_ids={"a"},
        timezone="UTC",
    )
    assert result.source_ids == ["a"]
    assert len(result.follow_up_questions) == 1


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(EvidenceError):
        parse_final_result(
            raw({"source_ids": ["invented"]}),
            operation_id=uuid4(),
            allowed_ids={"a"},
            timezone="UTC",
        )


def test_missing_marker_is_rejected() -> None:
    with pytest.raises(EvidenceError):
        parse_final_result("text only", operation_id=uuid4(), allowed_ids=set(), timezone="UTC")


def test_marker_filter_never_leaks_structured_tail() -> None:
    value = MarkerFilter()
    visible = "".join(value.feed(chunk) for chunk in ["Olá ", "<<<RE", "SULT>>>", '{"x":1}'])
    visible += value.flush()
    assert visible == "Olá "
    assert value.marker_seen


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
