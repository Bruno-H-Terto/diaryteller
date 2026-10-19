"""Durable context deletion requests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.feed import DeletionView

from exchange.models.ports.contexts import ContextRepository, DeletionRepository

from .views import deletion_view


async def request_context_deletion(
    *,
    owner_id: uuid.UUID,
    context_id: uuid.UUID,
    contexts: ContextRepository,
    deletions: DeletionRepository,
    deadline_seconds: int,
    now: datetime,
) -> DeletionView:
    """Create one deletion per context; retries return the same request."""
    copy = await contexts.by_id(owner_id, context_id)
    if copy is None:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Context not found")
    if copy.deletion_id is not None:
        existing = await deletions.by_id(owner_id, copy.deletion_id)
        if existing is not None:
            return deletion_view(existing)
    deletion = await deletions.create(
        owner_id,
        "context",
        context_id,
        now,
        now + timedelta(seconds=deadline_seconds),
    )
    await contexts.mark_delete_pending(owner_id, context_id, deletion.id, now)
    return deletion_view(deletion)


async def get_deletion(
    *, owner_id: uuid.UUID, deletion_id: uuid.UUID, deletions: DeletionRepository
) -> DeletionView:
    """Return the purge status only for its owner."""
    deletion = await deletions.by_id(owner_id, deletion_id)
    if deletion is None:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Deletion not found")
    return deletion_view(deletion)
