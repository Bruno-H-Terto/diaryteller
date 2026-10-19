"""Durable transcription job contracts.

A job is immutable; retry creates a new attempt that references the previous
one and reuses the validated media copy without reupload.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TranscriptionJobState(StrEnum):
    """Job lifecycle; only one terminal transition wins."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INDETERMINATE = "INDETERMINATE"


TERMINAL_JOB_STATES = frozenset(
    {
        TranscriptionJobState.SUCCEEDED,
        TranscriptionJobState.FAILED,
        TranscriptionJobState.CANCELLED,
        TranscriptionJobState.INDETERMINATE,
    }
)


class TranscriptionJobCreate(BaseModel):
    """Submit one transcription over a validated media copy."""

    model_config = ConfigDict(extra="forbid")

    client_job_id: UUID
    context_id: UUID
    media_id: UUID
    local_media_id: UUID
    language: str | None = Field(default=None, max_length=20)


class TranscriptionJobRetry(BaseModel):
    """Explicit retry; the user accepts possible duplicate provider cost."""

    model_config = ConfigDict(extra="forbid")

    client_job_id: UUID
    accept_duplicate_processing_risk: bool


class TranscriptionJobView(BaseModel):
    """Job state safe for the phone and for internal polling."""

    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    operation_id: UUID
    context_id: UUID
    media_id: UUID
    local_media_id: UUID
    parent_job_id: UUID | None
    attempt: int = Field(ge=1)
    state: TranscriptionJobState
    retryable: bool
    failure_code: str | None
    result_id: UUID | None
    created_at: datetime
    expires_at: datetime | None


class TranscriptSegment(BaseModel):
    """Optional provider segment with millisecond bounds."""

    model_config = ConfigDict(extra="forbid")

    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str


class TranscriptPayload(BaseModel):
    """Immutable transcript tied to the local original."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["transcription"] = "transcription"
    text: str
    language: str | None
    audio_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    media_id: UUID
    local_media_id: UUID
    job_id: UUID
    segments: list[TranscriptSegment] = Field(default_factory=list)
