"""Local records selected by the phone and sent for one operation.

Records are untrusted data. They are validated structurally, never persisted and
never used to authorize access to any other record or user.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_RECORDS = 50
MAX_RECORD_CHARS = 20_000
MAX_CONTEXT_CHARS = 50_000


class SourceType(StrEnum):
    """Origin of a record inside the phone's local store."""

    DIARY_TEXT = "diary_text"
    VOICE_TRANSCRIPTION = "voice_transcription"
    NOTE = "note"
    LOCAL_SUMMARY = "local_summary"


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ValueError("timestamps must include a timezone offset")
    return value


class ContextRecord(BaseModel):
    """One immutable record supplied by the client."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    recorded_at: datetime
    event_at: datetime | None = None
    text: str = Field(min_length=1, max_length=MAX_RECORD_CHARS)
    source_type: SourceType = SourceType.DIARY_TEXT

    _recorded = field_validator("recorded_at")(_require_timezone)
    _event = field_validator("event_at")(_require_timezone)


class ContextBundle(BaseModel):
    """Validated set of records with explicit coverage and unique IDs."""

    model_config = ConfigDict(extra="forbid")

    coverage: str = Field(default="selected_records", pattern="^selected_records$")
    records: list[ContextRecord] = Field(default_factory=list, max_length=MAX_RECORDS)

    @model_validator(mode="after")
    def _unique_and_bounded(self) -> ContextBundle:
        ids = [record.id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("context record ids must be unique")
        total = sum(len(record.text) for record in self.records)
        if total > MAX_CONTEXT_CHARS:
            raise ValueError("context text exceeds the character limit")
        return self

    def ids(self) -> set[str]:
        """Return the authorized set of local record IDs."""
        return {record.id for record in self.records}

    def by_id(self, record_id: str) -> ContextRecord | None:
        """Look up one record inside the authorized set."""
        return next((record for record in self.records if record.id == record_id), None)
