"""Operational change feed, snapshots and durable deletion contracts.

The feed is not diary synchronization. It only reports remote resources the
user sent, with minimal metadata and no content body.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResourceType(StrEnum):
    """Remote resources visible to the operational feed."""

    CONTEXT = "context"
    UPLOAD = "upload"
    JOB = "job"
    RESULT = "result"


class ChangeAction(StrEnum):
    """Upsert or tombstone for one resource."""

    UPSERT = "upsert"
    DELETE = "delete"


class Change(BaseModel):
    """One owner-scoped feed event without a content body."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    resource_type: ResourceType
    resource_id: UUID
    action: ChangeAction
    occurred_at: datetime
    revision: int = Field(ge=1)


class ChangesPage(BaseModel):
    """Cursor page of operational changes."""

    model_config = ConfigDict(extra="forbid")

    changes: list[Change]
    next_cursor: str | None
    has_more: bool


class SnapshotView(BaseModel):
    """Short-lived snapshot handle created after cursor expiry."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: UUID
    expires_at: datetime


class RemoteManifest(BaseModel):
    """Minimal manifest entry for a remote resource still alive."""

    model_config = ConfigDict(extra="forbid")

    resource_type: ResourceType
    resource_id: UUID
    revision: int = Field(ge=1)
    state: str
    expires_at: datetime | None


class SnapshotPage(BaseModel):
    """Stable page; `resume_cursor` ends the snapshot when null."""

    model_config = ConfigDict(extra="forbid")

    items: list[RemoteManifest]
    next_cursor: str | None
    has_more: bool
    resume_cursor: str | None


class DeletionState(StrEnum):
    """Durable purge lifecycle."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"


class DeletionView(BaseModel):
    """Deletion status without the deleted content."""

    model_config = ConfigDict(extra="forbid")

    deletion_id: UUID
    state: DeletionState
    requested_at: datetime
    purge_deadline: datetime
    completed_at: datetime | None


class InternalChange(BaseModel):
    """Trusted service request to record a job or result change."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    owner_id: UUID
    resource_type: ResourceType
    resource_id: UUID
    action: ChangeAction
    revision: int = Field(ge=1)
    occurred_at: datetime
