"""Keep the diary actions a reply may apply, dropping invented references.

The visible answer survives a malformed action: only the action is discarded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from diary_contracts.diary import DiarySnapshot
from diary_contracts.diary_actions import (
    CURRENT_RECORD,
    MAX_ACTIONS,
    CreateEntity,
    CreateEvent,
    DiaryAction,
    rejects,
)
from pydantic import TypeAdapter, ValidationError


@dataclass(frozen=True, slots=True)
class KeptActions:
    """Actions the phone may apply, plus how many were discarded."""

    actions: list[Any]
    ignored: int


def kept_actions(
    values: list[dict[str, Any]], snapshot: DiarySnapshot, allowed_ids: set[str]
) -> KeptActions:
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
        if isinstance(action, CreateEvent):
            # A guessed record id is not evidence; drop the reference, not the event.
            action.source_ids = [
                source
                for source in action.source_ids
                if source in allowed_ids or source == CURRENT_RECORD
            ]
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
    return KeptActions(actions=kept, ignored=len(values) - len(kept))
