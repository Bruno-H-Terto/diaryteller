"""Public context copy routes under `/v1/exchange`."""

from __future__ import annotations

from uuid import UUID

from diary_contracts.context_ref import ContextCreate, ContextView, RetentionUpdate
from diary_contracts.feed import DeletionView
from fastapi import APIRouter, Depends, Header, Response, status

from exchange.adapters.http.dependencies import (
    Repositories,
    get_container,
    get_principal,
    get_repositories,
)
from exchange.application.ports.identity import Principal
from exchange.application.use_cases.contexts import (
    create_context,
    get_context,
    parse_etag,
    seal_context,
    update_retention,
)
from exchange.application.use_cases.deletions import get_deletion, request_context_deletion
from exchange.container import Container
from exchange.util import utcnow

router = APIRouter(prefix="/exchange", tags=["exchange"])


def _document(view: ContextView, status_code: int = 200) -> Response:
    headers = {
        "ETag": f'"ctx-{view.revision}"',
        "Location": f"/v1/exchange/contexts/{view.context_id}",
    }
    return Response(
        content=view.model_dump_json(),
        status_code=status_code,
        media_type="application/json",
        headers=headers,
    )


@router.post("/contexts", status_code=status.HTTP_201_CREATED)
async def create(
    body: ContextCreate,
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> Response:
    """Create an authorized copy once per `client_context_id`."""
    settings = container.settings
    view, created = await create_context(
        owner_id=principal.user_id,
        body=body,
        contexts=repos.contexts,
        blobs=container.blobs,
        master_key=settings.context_encryption_key,
        max_bytes=settings.context_max_bytes,
        now=utcnow(),
    )
    return _document(view, status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@router.get("/contexts/{context_id}")
async def read(
    context_id: UUID,
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Return the owner's manifest without texts."""
    view = await get_context(
        owner_id=principal.user_id, context_id=context_id, contexts=repos.contexts
    )
    return _document(view)


@router.patch("/contexts/{context_id}/retention")
async def retention(
    context_id: UUID,
    body: RetentionUpdate,
    if_match: str | None = Header(default=None, alias="If-Match"),
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Change only the retention policy, guarded by `If-Match`."""
    view = await update_retention(
        owner_id=principal.user_id,
        context_id=context_id,
        body=body,
        expected_revision=parse_etag(if_match),
        contexts=repos.contexts,
        now=utcnow(),
    )
    return _document(view)


@router.post("/contexts/{context_id}/seal")
async def seal(
    context_id: UUID,
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Seal a draft copy; repeating the call is idempotent."""
    view = await seal_context(
        owner_id=principal.user_id, context_id=context_id, contexts=repos.contexts, now=utcnow()
    )
    return _document(view)


@router.delete("/contexts/{context_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete(
    context_id: UUID,
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> Response:
    """Request durable deletion of the copy."""
    settings = container.settings
    deletion = await request_context_deletion(
        owner_id=principal.user_id,
        context_id=context_id,
        contexts=repos.contexts,
        deletions=repos.deletions,
        deadline_seconds=settings.context_purge_deadline_seconds,
        now=utcnow(),
    )
    return Response(
        content=deletion.model_dump_json(),
        status_code=status.HTTP_202_ACCEPTED,
        media_type="application/json",
        headers={"Location": f"/v1/exchange/deletions/{deletion.deletion_id}"},
    )


@router.get("/deletions/{deletion_id}", response_model=DeletionView)
async def read_deletion(
    deletion_id: UUID,
    principal: Principal = Depends(get_principal),
    repos: Repositories = Depends(get_repositories),
) -> DeletionView:
    """Return the purge status of a deletion."""
    return await get_deletion(
        owner_id=principal.user_id, deletion_id=deletion_id, deletions=repos.deletions
    )
