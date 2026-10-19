"""Recoverable result payloads, proposals and acknowledgement.

Results are immutable and temporary (24 h by default). The phone acknowledges
after persisting locally; acknowledgement is not acceptance of a proposal.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .context_ref import EventPrecision, LocalSource
from .job import TranscriptPayload


class ProposalKind(StrEnum):
    """Kinds the phone may accept, edit and store locally."""

    ORGANIZED_TEXT = "organized_text"
    TIMELINE = "timeline"
    QUESTION = "question"
    REPLY = "reply"
    GOAL = "goal"
    REMINDER = "reminder"


class ProposalV2(BaseModel):
    """Proposal never applied by the backend."""

    model_config = ConfigDict(extra="forbid")

    proposal_id: UUID
    kind: ProposalKind
    text: str
    base_sources: list[LocalSource] = Field(default_factory=list)
    requires_confirmation: Literal[True] = True


class TimelineItemV2(BaseModel):
    """Event with explicit precision; `recorded_at` is never the event date."""

    model_config = ConfigDict(extra="forbid")

    text: str
    event_at: datetime | None
    event_date: date | None
    event_precision: EventPrecision
    sources: list[LocalSource] = Field(default_factory=list)


class ConversationPayload(BaseModel):
    """Answer, sources and local-only proposals."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["conversation"] = "conversation"
    answer: str
    sources: list[LocalSource] = Field(default_factory=list)
    proposals: list[ProposalV2] = Field(default_factory=list)
    timeline: list[TimelineItemV2] = Field(default_factory=list)
    coverage: str = Field(default="selected_context", pattern="^selected_context$")
    warnings: list[str] = Field(default_factory=list)


ResultPayload = Annotated[
    TranscriptPayload | ConversationPayload,
    Field(discriminator="kind"),
]


class ResultView(BaseModel):
    """Immutable result metadata plus typed payload."""

    model_config = ConfigDict(extra="forbid")

    result_id: UUID
    operation_id: UUID
    context_id: UUID
    created_at: datetime
    expires_at: datetime
    payload_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    payload: ResultPayload


class ResultAck(BaseModel):
    """Confirmation that the phone persisted the payload locally."""

    model_config = ConfigDict(extra="forbid")

    client_saved_at: datetime
    payload_sha256: str = Field(pattern="^[a-f0-9]{64}$")


class ResultSummary(BaseModel):
    """Metadata referenced by feed without payload content."""

    model_config = ConfigDict(extra="forbid")

    result_id: UUID
    operation_id: UUID
    context_id: UUID
    created_at: datetime
    expires_at: datetime
    payload_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    kind: str


class ResultEnvelope(BaseModel):
    """Internal creation request for one immutable result."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    context_id: UUID
    operation_id: UUID
    payload: dict[str, Any]
    ttl_seconds: int = Field(default=86_400, ge=60, le=172_800)
