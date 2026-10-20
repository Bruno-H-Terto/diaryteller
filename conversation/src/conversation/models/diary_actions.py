"""Keep the diary actions a reply may apply, dropping invented references.

The visible answer survives a malformed action: only the action is discarded.
"""

from __future__ import annotations

from typing import Any

from diary_contracts.diary import DiarySnapshot
from diary_contracts.diary_actions import (
    MAX_ACTIONS,
    CreateEntity,
    CreateEvent,
    DiaryAction,
    rejects,
)
from pydantic import TypeAdapter, ValidationError


def kept_actions(
    values: list[dict[str, Any]], snapshot: DiarySnapshot, allowed_ids: set[str]
) -> list[Any]:
    """Parse each action and keep only those pointing at provided identities.

    Actions may declare refs in any order, so the declared identifiers are
    collected first. A malformed or invented reference drops that action alone.
    """
    parsed: list[Any] = []
    for value in values[:MAX_ACTIONS]:
        try:
            parsed.append(TypeAdapter(DiaryAction).validate_python(value))
        except ValidationError:
            continue
    known_entities = snapshot.entity_ids() | {a.ref for a in parsed if isinstance(a, CreateEntity)}
    known_events = snapshot.event_ids() | {a.ref for a in parsed if isinstance(a, CreateEvent)}
    kept: list[Any] = []
    for action in parsed:
        if isinstance(action, CreateEvent) and set(action.participants) - known_entities:
            continue
        if rejects(
            action,
            snapshot=snapshot,
            allowed_source_ids=allowed_ids,
            entities=known_entities,
            events=known_events,
        ):
            continue
        kept.append(action)
    return kept
