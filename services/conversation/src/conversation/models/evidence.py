"""Validate structured results against the records actually provided.

A source reference is accepted only when the ID belongs to the operation's
context. A valid reference does not prove the interpretation is correct.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from diary_contracts.conversation import FinalResult
from diary_contracts.suggestions import (
    GoalProposal,
    LocalSummaryProposal,
    Proposal,
    ReminderProposal,
    TimelineEntry,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .response import MARKER


class EvidenceError(ValueError):
    """The model produced a result that cannot be trusted."""


class _Tail(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_ids: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    suggested_replies: list[str] = Field(default_factory=list)
    proposals: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _require_subset(ids: list[str], allowed: set[str]) -> None:
    unknown = set(ids) - allowed
    if unknown:
        raise EvidenceError("result references unknown source ids")


def _proposal(value: dict[str, Any], allowed: set[str], timezone: str) -> Proposal:
    kind = str(value.get("type", ""))
    sources = [str(item) for item in value.get("source_ids", [])]
    _require_subset(sources, allowed)
    text = str(value.get("text", "")).strip()
    if not text:
        raise EvidenceError("proposal text is empty")
    common = {
        "id": uuid4(),
        "text": text[:1000],
        "source_ids": sources,
        "requires_confirmation": True,
    }
    if kind == "goal":
        return GoalProposal(**common)
    if kind == "reminder":
        proposed = value.get("proposed_at")
        return ReminderProposal(
            **common,
            timezone=str(value.get("timezone") or timezone),
            proposed_at=datetime.fromisoformat(proposed) if proposed else None,
            needs_clarification=bool(value.get("needs_clarification", not proposed)),
        )
    if kind == "local_summary":
        start = value.get("period_start")
        end = value.get("period_end")
        return LocalSummaryProposal(
            **common,
            period_start=date.fromisoformat(start) if start else None,
            period_end=date.fromisoformat(end) if end else None,
        )
    raise EvidenceError("unknown proposal type")


def _timeline(value: dict[str, Any], allowed: set[str]) -> TimelineEntry:
    sources = [str(item) for item in value.get("source_ids", [])]
    _require_subset(sources, allowed)
    event_date = value.get("event_date")
    recorded = value.get("recorded_at")
    return TimelineEntry(
        event=str(value.get("event", ""))[:1000],
        event_date=date.fromisoformat(event_date) if event_date else None,
        recorded_at=datetime.fromisoformat(recorded) if recorded else None,
        source_ids=sources,
        uncertainty=(str(value["uncertainty"])[:300] if value.get("uncertainty") else None),
    )


def parse_final_result(
    raw_text: str,
    *,
    operation_id: UUID,
    allowed_ids: set[str],
    timezone: str,
    timeline_override: list[dict[str, Any]] | None = None,
) -> FinalResult:
    """Split visible answer and structured tail, then validate every reference."""
    index = raw_text.rfind(MARKER)
    if index < 0:
        raise EvidenceError("structured result marker missing")
    answer = raw_text[:index].strip()
    if not answer:
        raise EvidenceError("answer is empty")
    try:
        tail = _Tail.model_validate(json.loads(raw_text[index + len(MARKER) :]))
    except (ValueError, ValidationError) as exc:
        raise EvidenceError("invalid structured result") from exc
    _require_subset(tail.source_ids, allowed_ids)
    timeline_values = timeline_override if timeline_override is not None else tail.timeline
    try:
        proposals = [_proposal(item, allowed_ids, timezone) for item in tail.proposals[:10]]
        timeline = [_timeline(item, allowed_ids) for item in timeline_values[:100]]
    except (ValueError, TypeError) as exc:
        raise EvidenceError("invalid proposal or timeline") from exc
    return FinalResult(
        operation_id=operation_id,
        answer=answer,
        source_ids=tail.source_ids[:50],
        follow_up_questions=tail.follow_up_questions[:2],
        suggested_replies=tail.suggested_replies[:5],
        proposals=proposals,
        timeline=timeline,
        warnings=tail.warnings[:10],
    )


def timeline_from_tool(value: dict[str, Any], allowed_ids: set[str]) -> list[dict[str, Any]]:
    """Convert a `build_timeline` result into validated tail dictionaries."""
    entries: list[dict[str, Any]] = []
    for group in ("events", "undated"):
        for item in value.get(group, []) if isinstance(value.get(group), list) else []:
            if not isinstance(item, dict):
                continue
            sources = [str(source) for source in item.get("source_ids", [])]
            _require_subset(sources, allowed_ids)
            entries.append(
                {
                    "event": item.get("event", ""),
                    "event_date": item.get("event_date"),
                    "recorded_at": item.get("recorded_at"),
                    "source_ids": sources,
                    "uncertainty": item.get("uncertainty"),
                }
            )
    return entries
