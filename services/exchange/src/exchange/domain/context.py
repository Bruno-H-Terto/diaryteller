"""Authorized context copies; the phone keeps the original diary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from diary_contracts.context_ref import ContextPurpose, ContextState, RetentionPolicy


@dataclass(frozen=True, slots=True)
class ContextCopy:
    """Stored manifest for one authorized copy."""

    id: UUID
    owner_id: UUID
    client_context_id: UUID
    state: ContextState
    purpose: ContextPurpose
    retention_policy: RetentionPolicy
    revision: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    storage_key: str
    content_sha256: str
    record_count: int
    text_bytes: int
    deletion_id: UUID | None

    @property
    def etag(self) -> str:
        """Opaque revision used by `If-Match`."""
        return f'"ctx-{self.revision}"'


@dataclass(frozen=True, slots=True)
class ContextSource:
    """Local provenance for one selected record."""

    context_id: UUID
    local_record_id: UUID
    local_version_id: UUID
    content_sha256: str


@dataclass(frozen=True, slots=True)
class Deletion:
    """Durable purge request shared by contexts, uploads and results."""

    id: UUID
    owner_id: UUID
    resource_type: str
    resource_id: UUID
    state: str
    requested_at: datetime
    purge_deadline: datetime
    completed_at: datetime | None
