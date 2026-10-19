"""Persistence ports for context copies and deletions."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from diary_contracts.context_ref import RetentionPolicy

from exchange.domain.context import ContextCopy, ContextSource, Deletion


class ContextRepository(Protocol):
    """Owner-scoped context persistence."""

    async def by_client_id(self, owner_id: UUID, client_context_id: UUID) -> ContextCopy | None:
        """Find an idempotent copy by the client-provided id."""
        ...

    async def by_id(self, owner_id: UUID, context_id: UUID) -> ContextCopy | None:
        """Load a copy only when it belongs to the owner."""
        ...

    async def create(self, copy: ContextCopy, sources: list[ContextSource]) -> bool:
        """Insert the copy; False when an idempotent row already exists."""
        ...

    async def sources(self, context_id: UUID) -> list[ContextSource]:
        """List local provenance for one copy."""
        ...

    async def update_retention(
        self,
        owner_id: UUID,
        context_id: UUID,
        policy: RetentionPolicy,
        expected_revision: int,
        now: datetime,
    ) -> ContextCopy | None:
        """Compare-and-set the retention policy and revision."""
        ...

    async def seal(self, owner_id: UUID, context_id: UUID, now: datetime) -> ContextCopy | None:
        """Move a draft copy to READY exactly once."""
        ...

    async def mark_delete_pending(
        self, owner_id: UUID, context_id: UUID, deletion_id: UUID, now: datetime
    ) -> None:
        """Block promotion while the purge is pending."""
        ...


class DeletionRepository(Protocol):
    """Durable deletion requests."""

    async def create(
        self,
        owner_id: UUID,
        resource_type: str,
        resource_id: UUID,
        now: datetime,
        purge_deadline: datetime,
    ) -> Deletion:
        """Insert a PENDING deletion."""
        ...

    async def by_id(self, owner_id: UUID, deletion_id: UUID) -> Deletion | None:
        """Load a deletion only for its owner."""
        ...
