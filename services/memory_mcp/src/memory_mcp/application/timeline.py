"""Deterministic timeline built from explicit event dates."""

from __future__ import annotations

from diary_contracts.context import ContextRecord
from diary_contracts.mcp import TimelineToolEntry, TimelineToolResult


def build_timeline(records: list[ContextRecord]) -> TimelineToolResult:
    """Sort dated events and keep undated records separate."""
    dated: list[tuple[ContextRecord, TimelineToolEntry]] = []
    undated: list[TimelineToolEntry] = []
    for record in records:
        entry = TimelineToolEntry(
            event=record.text[:500],
            event_date=record.event_at.date().isoformat() if record.event_at else None,
            recorded_at=record.recorded_at,
            source_ids=[record.id],
            uncertainty=(
                None
                if record.event_at
                else "Data do evento não informada; recorded_at não é a data do fato."
            ),
        )
        if record.event_at is not None:
            dated.append((record, entry))
        else:
            undated.append(entry)
    dated.sort(key=lambda item: item[1].event_date or "")
    return TimelineToolResult(
        events=[entry for _, entry in dated],
        undated=undated,
        source_ids=[record.id for record in records],
    )
