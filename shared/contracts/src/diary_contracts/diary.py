"""Snapshot of the local diary sent with a conversation turn.

The server receives only what the phone chose to send, uses it for one turn and
never stores it. Identifiers are local to the device.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

MAX_ENTITIES = 60
MAX_EVENTS = 40
MAX_DRAFT_CHARS = 4000


class Precision(StrEnum):
    """Date precision of an event, mirroring the local model."""

    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    UNKNOWN = "unknown"


class EntityKind(StrEnum):
    """Entity kinds the registry accepts; the owner is never created here."""

    PERSON = "person"
    ANIMAL = "animal"
    PLACE = "place"


class SnapshotEntity(BaseModel):
    """One entity the phone already has, so the model can reuse it."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    kind: EntityKind
    name: str = Field(min_length=1, max_length=80)
    relation: str = Field(default="", max_length=80)


class SnapshotEvent(BaseModel):
    """One event the phone already has, so the model can point at it."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=120)
    event_date: date | None = None
    precision: Precision = Precision.UNKNOWN


class DiarySnapshot(BaseModel):
    """Local state sent with the turn: never stored by the server."""

    model_config = ConfigDict(extra="forbid")

    entities: list[SnapshotEntity] = Field(default_factory=list, max_length=MAX_ENTITIES)
    events: list[SnapshotEvent] = Field(default_factory=list, max_length=MAX_EVENTS)
    draft: str = Field(default="", max_length=MAX_DRAFT_CHARS)
    today: date | None = None

    def entity_ids(self) -> set[str]:
        """Local entity ids the model may reference."""
        return {entity.id for entity in self.entities}

    def event_ids(self) -> set[str]:
        """Local event ids the model may reference."""
        return {event.id for event in self.events}
