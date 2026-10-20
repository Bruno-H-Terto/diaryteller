"""Diary actions a conversation may produce for the phone to apply locally.

The server never writes diary content. Each action is a proposal: the phone
validates it, applies it to its own database and decides the review state from
the certainty the model declared. References are restricted to entities and
events the phone sent in the snapshot, or to the new refs declared in the same
response, so the model cannot invent identities.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .diary import DiarySnapshot, EntityKind, Precision

MAX_ACTIONS = 12
NEW_REF = r"^new:[a-z0-9-]{1,24}$"
#: Values a model writes when it means "no date"; they are not dates.
NO_DATE = {"", "unknown", "undated", "none", "null", "sem data", "n/a"}


class ActionKind(StrEnum):
    """Discriminator values for diary actions."""

    CREATE_ENTITY = "create_entity"
    CREATE_EVENT = "create_event"
    LINK_ENTITY = "link_entity"
    SET_EVENT_DATE = "set_event_date"


class ActionCertainty(StrEnum):
    """How the fact reached the model; the phone maps it to a review state."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"


class CreateEntity(BaseModel):
    """A new person, animal or place the conversation introduced."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[ActionKind.CREATE_ENTITY] = ActionKind.CREATE_ENTITY
    ref: str = Field(pattern=NEW_REF)
    entity_kind: EntityKind
    name: str = Field(min_length=1, max_length=80)
    relation: str = Field(default="", max_length=80)
    certainty: ActionCertainty = ActionCertainty.EXPLICIT


class CreateEvent(BaseModel):
    """An event built from what was narrated, with its participants."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[ActionKind.CREATE_EVENT] = ActionKind.CREATE_EVENT
    ref: str = Field(pattern=NEW_REF)
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=600)
    event_date: date | None = None
    precision: Precision = Precision.UNKNOWN
    participants: list[str] = Field(default_factory=list, max_length=10)
    source_ids: list[str] = Field(default_factory=list, max_length=20)
    certainty: ActionCertainty = ActionCertainty.EXPLICIT

    @field_validator("event_date", mode="before")
    @classmethod
    def _no_placeholder_date(cls, value: object) -> object:
        if isinstance(value, str) and value.strip().lower() in NO_DATE:
            return None
        return value

    @model_validator(mode="after")
    def _date_matches_precision(self) -> CreateEvent:
        if self.event_date is None and self.precision is not Precision.UNKNOWN:
            raise ValueError("an event without a date must use unknown precision")
        return self


class LinkEntity(BaseModel):
    """A mention of an entity in a record or an event."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[ActionKind.LINK_ENTITY] = ActionKind.LINK_ENTITY
    entity: str = Field(min_length=1, max_length=128)
    source_id: str | None = Field(default=None, max_length=128)
    event: str | None = Field(default=None, max_length=128)
    certainty: ActionCertainty = ActionCertainty.EXPLICIT

    @model_validator(mode="after")
    def _has_target(self) -> LinkEntity:
        if not self.source_id and not self.event:
            raise ValueError("a link needs a record or an event")
        return self


class SetEventDate(BaseModel):
    """A correction of when an event happened."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[ActionKind.SET_EVENT_DATE] = ActionKind.SET_EVENT_DATE
    event: str = Field(min_length=1, max_length=128)
    event_date: date
    precision: Precision
    certainty: ActionCertainty = ActionCertainty.EXPLICIT


DiaryAction = Annotated[
    CreateEntity | CreateEvent | LinkEntity | SetEventDate,
    Field(discriminator="kind"),
]


def rejects(
    action: DiaryAction,
    *,
    snapshot: DiarySnapshot,
    allowed_source_ids: set[str],
    entities: set[str],
    events: set[str],
) -> bool:
    """Whether one action points outside what the phone sent or declared."""
    if isinstance(action, CreateEntity):
        return False
    if isinstance(action, CreateEvent):
        return bool(
            (set(action.participants) - entities) or (set(action.source_ids) - allowed_source_ids)
        )
    if isinstance(action, LinkEntity):
        return bool(
            (set([action.entity]) - entities)
            or (set([action.event]) - events if action.event else set())
            or (set([action.source_id]) - allowed_source_ids if action.source_id else set())
        )
    return bool(set([action.event]) - snapshot.event_ids())


def validated_actions(
    actions: list[DiaryAction],
    *,
    snapshot: DiarySnapshot,
    allowed_source_ids: set[str],
) -> list[DiaryAction]:
    """Reject actions that reference identities or records not provided."""
    entities = snapshot.entity_ids()
    events = snapshot.event_ids()
    new_entities = {a.ref for a in actions if isinstance(a, CreateEntity)}
    new_events = {a.ref for a in actions if isinstance(a, CreateEvent)}
    if len(new_entities) != sum(isinstance(a, CreateEntity) for a in actions):
        raise ValueError("duplicate create_entity ref")
    if len(new_events) != sum(isinstance(a, CreateEvent) for a in actions):
        raise ValueError("duplicate create_event ref")
    for action in actions:
        if rejects(
            action,
            snapshot=snapshot,
            allowed_source_ids=allowed_source_ids,
            entities=entities | new_entities,
            events=events | new_events,
        ):
            raise ValueError("unknown reference in action")
    return actions
