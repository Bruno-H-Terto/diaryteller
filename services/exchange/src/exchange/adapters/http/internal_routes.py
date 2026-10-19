"""Internal exchange routes used only by trusted services."""

from __future__ import annotations

from uuid import UUID

from diary_contracts.context_ref import InternalContextRecords
from fastapi import APIRouter, Depends

from exchange.adapters.http.dependencies import (
    Repositories,
    get_container,
    get_repositories,
    require_internal_service,
)
from exchange.application.use_cases.contexts import read_records
from exchange.container import Container

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_service)],
)


@router.get("/contexts/{context_id}", response_model=InternalContextRecords)
async def context_records(
    context_id: UUID,
    owner_id: UUID,
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> InternalContextRecords:
    """Decrypt one owner's ready copy for conversation or speech."""
    records = await read_records(
        owner_id=owner_id,
        context_id=context_id,
        contexts=repos.contexts,
        blobs=container.blobs,
        master_key=container.settings.context_encryption_key,
    )
    copy = await repos.contexts.by_id(owner_id, context_id)
    return InternalContextRecords(
        context_id=context_id,
        content_sha256=copy.content_sha256 if copy else "",
        records=records,
    )
