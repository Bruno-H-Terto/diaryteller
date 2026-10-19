"""Owner-scoped operation metadata and cooperative cancellation."""

from __future__ import annotations

from uuid import UUID

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import OperationView
from fastapi import APIRouter, Depends, status

from identity.controllers.dependencies import (
    AuthContext,
    get_auth,
    get_repositories,
)
from identity.controllers.repositories import Repositories
from identity.services.common import utcnow
from identity.services.finish_operation import operation_view

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/{operation_id}", response_model=OperationView)
async def get_operation(
    operation_id: UUID,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> OperationView:
    """Return metadata only; an old answer is never replayed."""
    receipt = await repos.operations.by_id(operation_id, auth.user.id)
    if receipt is None:
        raise DomainError(ErrorCode.OPERATION_NOT_FOUND, 404, "Operation not found")
    return operation_view(receipt)


@router.post("/{operation_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_operation(
    operation_id: UUID,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> OperationView:
    """Request cooperative cancellation and return current state."""
    moment = utcnow()
    receipt = await repos.operations.by_id(operation_id, auth.user.id)
    if receipt is None:
        raise DomainError(ErrorCode.OPERATION_NOT_FOUND, 404, "Operation not found")
    await repos.control.request_cancel(operation_id, auth.user.id, moment)
    current = await repos.operations.by_id(operation_id, auth.user.id)
    return operation_view(current or receipt)
