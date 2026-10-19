"""Authorized context copies and local provenance references.

The phone owns originals and versions. These models carry only the records the
user explicitly selected for one operation; IDs are provenance, never remote
authority. Server-side `revision` is copy state, not a diary version number.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_RECORDS = 50
MAX_RECORD_CHARS = 50_000


class EventPrecision(StrEnum):
    """How precisely the user dated the event."""

    UNKNOWN = "unknown"
    DATE = "date"
    DATETIME = "datetime"
    APPROXIMATE = "approximate"


class RetentionPolicy(StrEnum):
    """Explicit retention choice; there is no silent default."""

    DELETE_AFTER_PROCESSING = "delete_after_processing"
    KEEP_UNTIL_DELETED = "keep_until_deleted"


class ContextState(StrEnum):
    """Lifecycle of an authorized copy."""

    DRAFT = "DRAFT"
    READY = "READY"
    DELETE_PENDING = "DELETE_PENDING"
    DELETED = "DELETED"


class ContextPurpose(StrEnum):
    """Allowed reasons to create a copy."""

    TRANSCRIBE = "transcribe"
    CONVERSATION = "conversation"
    RECALL = "recall"
    ORGANIZE = "organize"
    TIMELINE = "timeline"
    SUMMARIZE = "summarize"


class LocalSource(BaseModel):
    """Stable local provenance for one record version."""

    model_config = ConfigDict(extra="forbid")

    local_record_id: UUID
    local_version_id: UUID
    content_sha256: str = Field(pattern="^[a-f0-9]{64}$")


class SelectedRecord(LocalSource):
    """A record the user explicitly selected, with its local text."""

    local_version_number: int = Field(ge=1)
    base_local_version_id: UUID | None
    text: str = Field(min_length=1, max_length=MAX_RECORD_CHARS)
    recorded_at: datetime
    event_at: datetime | None
    event_date: date | None
    event_description: str | None = Field(default=None, max_length=500)
    event_precision: EventPrecision
    timezone: str = Field(min_length=1, max_length=64)

    @field_validator("recorded_at", "event_at")
    @classmethod
    def _require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamps must include a timezone offset")
        return value

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("timezone must be a valid IANA name") from exc
        return value

    @model_validator(mode="after")
    def _precision_is_consistent(self) -> SelectedRecord:
        if self.event_date is not None and self.event_at is not None:
            raise ValueError("event_date and event_at are mutually exclusive")
        if self.event_precision is EventPrecision.DATETIME and self.event_at is None:
            raise ValueError("datetime precision requires event_at")
        if self.event_precision is EventPrecision.DATE and self.event_date is None:
            raise ValueError("date precision requires event_date")
        if (
            self.event_precision in {EventPrecision.DATE, EventPrecision.APPROXIMATE}
            and self.event_at is not None
        ):
            raise ValueError("only datetime precision may carry event_at")
        if self.event_precision is EventPrecision.UNKNOWN and (
            self.event_at or self.event_date or self.event_description
        ):
            raise ValueError("unknown precision must not assert a date")
        if (
            self.event_precision is EventPrecision.APPROXIMATE
            and self.event_date is None
            and not self.event_description
        ):
            raise ValueError("approximate precision requires a date or description")
        return self


class ContextCreate(BaseModel):
    """Request to create an authorized copy."""

    model_config = ConfigDict(extra="forbid")

    client_context_id: UUID
    purpose: ContextPurpose
    retention_policy: RetentionPolicy
    records: list[SelectedRecord] = Field(default_factory=list, max_length=MAX_RECORDS)

    @model_validator(mode="after")
    def _unique_records(self) -> ContextCreate:
        ids = [record.local_record_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("local_record_id must be unique inside a context")
        if self.purpose is ContextPurpose.TRANSCRIBE and self.records:
            raise ValueError("transcription contexts start without textual records")
        return self

    @property
    def text_bytes(self) -> int:
        """UTF-8 size of the selected text, used for upload quota."""
        return sum(len(record.text.encode("utf-8")) for record in self.records)


class ContextView(BaseModel):
    """Manifest and lifecycle metadata; texts are never returned here."""

    model_config = ConfigDict(extra="forbid")

    context_id: UUID
    client_context_id: UUID
    state: ContextState
    purpose: ContextPurpose
    retention_policy: RetentionPolicy
    revision: int = Field(ge=1)
    created_at: datetime
    expires_at: datetime | None
    sources: list[LocalSource]
    media_ids: list[UUID]
    deletion_id: UUID | None


class RetentionUpdate(BaseModel):
    """Explicit retention change; requires `If-Match` with the current revision."""

    model_config = ConfigDict(extra="forbid")

    retention_policy: RetentionPolicy
