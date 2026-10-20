"""Result/evidence validation tests."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from conversation.models.evidence import EvidenceError, parse_final_result
from conversation.models.response import MARKER, MarkerFilter


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


def test_empty_answer_is_rejected() -> None:
    with pytest.raises(EvidenceError):
        parse_final_result(MARKER + "{}", operation_id=uuid4(), allowed_ids=set(), timezone="UTC")


def test_marker_filter_never_leaks_structured_tail() -> None:
    value = MarkerFilter()
    visible = "".join(value.feed(chunk) for chunk in ["Olá ", "<<<RE", "SULT>>>", '{"x":1}'])
    visible += value.flush()
    assert visible == "Olá "
    assert value.marker_seen


def test_malformed_tail_keeps_the_answer_visible() -> None:
    result = parse_final_result(
        f"Resposta\n{MARKER}{{not json",
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
    )
    assert result.answer == "Resposta"
    assert result.actions == []
    assert "structured result unavailable" in result.warnings


def test_missing_marker_returns_the_answer_without_structure() -> None:
    result = parse_final_result(
        "Resposta sem marcador",
        operation_id=uuid4(),
        allowed_ids=set(),
        timezone="UTC",
    )
    assert result.answer == "Resposta sem marcador"
    assert result.actions == []
    assert result.warnings == ["structured result unavailable"]
