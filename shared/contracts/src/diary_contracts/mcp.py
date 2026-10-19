"""Internal MCP contracts: context credential, tool names and outputs.

The model may choose tool arguments, but the client injects `context_token`.
The server accepts only records embedded in that authenticated token.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .context import ContextRecord

CONTEXT_TOKEN_FIELD = "context_token"
MCP_AUDIENCE = "memory-mcp"
MCP_PURPOSE = "memory-context"
MAX_TOOL_CALLS = 4


class MemoryTool(StrEnum):
    """Allowlisted tools exposed by `memory_mcp`."""

    SEARCH = "search_memories"
    GET = "get_memory"
    ORGANIZE = "organize_ideas"
    TIMELINE = "build_timeline"
    SUMMARIZE = "summarize_period"


class ContextTokenClaims(BaseModel):
    """Short-lived, encrypted claims bound to one AI operation and record set."""

    model_config = ConfigDict(extra="forbid")

    aud: str = Field(default=MCP_AUDIENCE, pattern="^memory-mcp$")
    purpose: str = Field(default=MCP_PURPOSE, pattern="^memory-context$")
    operation_id: UUID
    user_id: UUID
    session_id: UUID
    permission: str
    records: list[ContextRecord] = Field(max_length=50)
    issued_at: datetime
    expires_at: datetime
    context_digest: str = Field(min_length=16, max_length=128)


class MemoryHit(BaseModel):
    """Lexical hit with provenance inside the supplied records."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    recorded_at: datetime
    event_at: datetime | None = None
    score: float = Field(ge=0)


class MemorySearchResult(BaseModel):
    """Results and explicit coverage of a lexical search."""

    model_config = ConfigDict(extra="forbid")

    query: str
    hits: list[MemoryHit]
    coverage: str = "provided_context"
    searched_records: int


class MemoryItem(BaseModel):
    """One authorized record."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    recorded_at: datetime
    event_at: datetime | None = None
    source_type: str


class OrganizedGroup(BaseModel):
    """Ideas grouped without adding facts."""

    model_config = ConfigDict(extra="forbid")

    label: str
    items: list[str]
    source_ids: list[str]


class OrganizedIdeas(BaseModel):
    """Organization result separating reports from suggestions."""

    model_config = ConfigDict(extra="forbid")

    reports: list[str]
    open_questions: list[str]
    next_steps: list[str]
    groups: list[OrganizedGroup]
    source_ids: list[str]
    coverage: str = "provided_context"


class TimelineToolEntry(BaseModel):
    """Dated event or an explicitly undated record."""

    model_config = ConfigDict(extra="forbid")

    event: str
    event_date: str | None = None
    recorded_at: datetime | None = None
    source_ids: list[str]
    uncertainty: str | None = None


class TimelineToolResult(BaseModel):
    """Ordered events plus undated items kept separately."""

    model_config = ConfigDict(extra="forbid")

    events: list[TimelineToolEntry]
    undated: list[TimelineToolEntry]
    source_ids: list[str]
    coverage: str = "provided_context"


class SummaryToolResult(BaseModel):
    """Summary that never claims to have read missing records."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    period_start: str | None = None
    period_end: str | None = None
    source_ids: list[str]
    coverage: str = "provided_context"
    warning: str = "Apenas os registros enviados foram considerados."
