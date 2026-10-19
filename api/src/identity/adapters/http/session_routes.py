"""Session management, push registration and notification routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from identity.adapters.http.dependencies import (
    AuthContext,
    get_auth,
    get_container,
    get_repositories,
)
from identity.adapters.http.repositories import Repositories
from identity.adapters.http.schemas_account import NotificationListResponse
from identity.adapters.http.schemas_auth import PushTokenRequest, SessionResponse
from identity.application.use_cases.manage_account import (
    delete_push_token,
    list_notifications,
    list_sessions,
    mark_notification_read,
    put_push_token,
    revoke_other_sessions,
    revoke_owned_session,
)
from identity.container import Container

router = APIRouter(tags=["sessions"])


@router.get("/me/sessions", response_model=list[SessionResponse])
async def sessions(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> list[SessionResponse]:
    """List the caller's sessions, including the current one."""
    values = await list_sessions(
        sessions=repos.sessions,
        user_id=auth.user.id,
        current_session_id=auth.session.id,
    )
    return [SessionResponse(**value) for value in values]


@router.delete("/me/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Revoke one session owned by the caller."""
    await revoke_owned_session(
        sessions=repos.sessions,
        security=repos.security,
        user_id=auth.user.id,
        session_id=session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/sessions/revoke-others", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_others(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Revoke every session except the current one."""
    await revoke_other_sessions(
        sessions=repos.sessions,
        security=repos.security,
        user_id=auth.user.id,
        current_session_id=auth.session.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/me/devices/{device_id}/push-token", status_code=status.HTTP_204_NO_CONTENT)
async def put_push(
    device_id: UUID,
    body: PushTokenRequest,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> Response:
    """Register a push token for a user-owned device."""
    await put_push_token(
        devices=repos.devices,
        push_repository=repos.push,
        push_key=container.settings.push_token_key,
        user_id=auth.user.id,
        device_id=device_id,
        token=body.token,
        platform=body.platform,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/devices/{device_id}/push-token", status_code=status.HTTP_204_NO_CONTENT)
async def delete_push(
    device_id: UUID,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Remove a push registration idempotently."""
    await delete_push_token(push_repository=repos.push, user_id=auth.user.id, device_id=device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/notifications", response_model=NotificationListResponse)
async def notifications(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
    limit: int = Query(default=20, ge=1, le=50),
    before: datetime | None = Query(default=None),
) -> NotificationListResponse:
    """List own administrative notifications, newest first."""
    items = await list_notifications(
        notifications=repos.notifications,
        user_id=auth.user.id,
        limit=limit,
        before=before,
    )
    next_before = items[-1]["created_at"] if len(items) == limit else None
    return NotificationListResponse(items=items, next_before=next_before)


@router.post(
    "/me/notifications/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def read_notification(
    notification_id: UUID,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> Response:
    """Mark an own notification as read."""
    await mark_notification_read(
        notifications=repos.notifications,
        user_id=auth.user.id,
        notification_id=notification_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
