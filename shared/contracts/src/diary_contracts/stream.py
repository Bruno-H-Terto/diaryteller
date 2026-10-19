"""SSE event contract for POST responses.

Every event carries the operation id and a strictly increasing sequence. Errors
after the stream opened are typed events because the HTTP status is already sent.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StreamEventType(StrEnum):
    """Event names documented for mobile clients."""

    STARTED = "started"
    TEXT_DELTA = "text_delta"
    TOOL_STATUS = "tool_status"
    RESULT = "result"
    ERROR = "error"
    COMPLETED = "completed"


class StreamEvent(BaseModel):
    """One typed SSE frame."""

    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    sequence: int = Field(ge=0)
    type: StreamEventType
    data: dict[str, Any] = Field(default_factory=dict)


class ErrorPayload(BaseModel):
    """Safe error data for an in-stream failure."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    retryable: bool = False


class ToolStatusPayload(BaseModel):
    """Progress about a tool call without arguments or private reasoning."""

    model_config = ConfigDict(extra="forbid")

    tool: str
    phase: Literal["started", "completed", "failed"]


class StartedPayload(BaseModel):
    """Marks the moment the reservation was authorized."""

    model_config = ConfigDict(extra="forbid")

    mode: str


class CompletedPayload(BaseModel):
    """Terminates a successful stream after the `result` event."""

    model_config = ConfigDict(extra="forbid")

    state: Literal["succeeded"] = "succeeded"


def encode_sse(event: StreamEvent) -> str:
    """Serialize one event using the `event:` and `data:` SSE fields."""
    body = {"operation_id": str(event.operation_id), "sequence": event.sequence, **event.data}
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event.type.value}\ndata: {payload}\nid: {event.sequence}\n\n"


def encode_comment(text: str = "keep-alive") -> str:
    """Serialize a comment frame used as heartbeat."""
    return f": {text}\n\n"
