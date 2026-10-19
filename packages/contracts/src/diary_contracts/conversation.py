"""Request and final result contracts for `/ai/responses`.

The mode expresses intent only. Entitlements are always evaluated by identity.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .context import ContextBundle
from .suggestions import Proposal, TimelineEntry


class ResponseMode(StrEnum):
    """Allowed intentions for a response."""

    CONVERSATION = "conversation"
    RECALL = "recall"
    ORGANIZE = "organize"
    TIMELINE = "timeline"
    SUMMARIZE = "summarize"


CONTEXT_MODES = frozenset(
    {
        ResponseMode.RECALL,
        ResponseMode.ORGANIZE,
        ResponseMode.TIMELINE,
        ResponseMode.SUMMARIZE,
    }
)


class ConversationRequest(BaseModel):
    """Body of a streaming AI request. Owner is derived from the session."""

    model_config = ConfigDict(extra="forbid")

    client_message_id: UUID
    conversation_id: str = Field(min_length=1, max_length=128)
    context_id: UUID | None = None
    mode: ResponseMode = ResponseMode.CONVERSATION
    message: str = Field(min_length=1, max_length=8000)
    locale: str = Field(default="pt-BR", max_length=16)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    context: ContextBundle = Field(default_factory=ContextBundle)

    @model_validator(mode="after")
    def _context_selection(self) -> ConversationRequest:
        inline = bool(self.context.records)
        if self.context_id is not None and inline:
            raise ValueError("context_id and inline context are mutually exclusive")
        if self.mode in CONTEXT_MODES and self.context_id is None and not inline:
            raise ValueError("this mode requires context_id or selected records")
        return self


class FinalResult(BaseModel):
    """Validated final result. Only this event enables actionable proposals."""

    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    answer: str = Field(min_length=1, max_length=20_000)
    coverage: str = Field(default="provided_context", pattern="^provided_context$")
    source_ids: list[str] = Field(default_factory=list, max_length=50)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=2)
    suggested_replies: list[str] = Field(default_factory=list, max_length=5)
    proposals: list[Proposal] = Field(default_factory=list, max_length=10)
    timeline: list[TimelineEntry] = Field(default_factory=list, max_length=100)
    warnings: list[str] = Field(default_factory=list, max_length=10)
