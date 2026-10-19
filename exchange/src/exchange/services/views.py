"""Mapping stored exchange rows to public contract views."""

from __future__ import annotations

from diary_contracts.context_ref import ContextView, LocalSource
from diary_contracts.feed import DeletionState, DeletionView

from exchange.models.context import ContextCopy, ContextSource, Deletion


def context_view(copy: ContextCopy, sources: list[ContextSource]) -> ContextView:
    """Return the manifest without record texts."""
    return ContextView(
        context_id=copy.id,
        client_context_id=copy.client_context_id,
        state=copy.state,
        purpose=copy.purpose,
        retention_policy=copy.retention_policy,
        revision=copy.revision,
        created_at=copy.created_at,
        expires_at=copy.expires_at,
        sources=[
            LocalSource(
                local_record_id=source.local_record_id,
                local_version_id=source.local_version_id,
                content_sha256=source.content_sha256,
            )
            for source in sources
        ],
        media_ids=[],
        deletion_id=copy.deletion_id,
    )


def deletion_view(deletion: Deletion) -> DeletionView:
    """Return the purge status without content."""
    return DeletionView(
        deletion_id=deletion.id,
        state=DeletionState(deletion.state),
        requested_at=deletion.requested_at,
        purge_deadline=deletion.purge_deadline,
        completed_at=deletion.completed_at,
    )
