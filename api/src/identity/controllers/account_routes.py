"""Account profile, entitlements, usage and deletion routes."""

from __future__ import annotations

from diary_contracts.authorization import EntitlementView
from fastapi import APIRouter, Depends, status

from identity.config.container import Container
from identity.controllers.dependencies import (
    AuthContext,
    get_auth,
    get_container,
    get_repositories,
)
from identity.controllers.repositories import Repositories
from identity.controllers.schemas_account import ProfileUpdate, UsageResponse
from identity.controllers.schemas_auth import ProfileResponse
from identity.services.common import utcnow
from identity.services.entitlements import evaluate_entitlement
from identity.services.manage_account import (
    request_account_deletion,
    update_profile,
)

router = APIRouter(tags=["account"])


@router.get("/me", response_model=ProfileResponse)
async def me(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> ProfileResponse:
    """Return the authenticated profile and account state."""
    profile = await repos.accounts.profile(auth.user.id)
    if profile is None:
        return ProfileResponse(
            id=auth.user.id,
            email=auth.user.email,
            display_name=None,
            locale="pt-BR",
            timezone="UTC",
            status=auth.user.status.value,
            email_verified=auth.user.email_verified_at is not None,
            created_at=auth.user.created_at,
            updated_at=auth.user.updated_at,
        )
    return ProfileResponse(
        id=auth.user.id,
        email=auth.user.email,
        display_name=profile.display_name,
        locale=profile.locale,
        timezone=profile.timezone,
        status=auth.user.status.value,
        email_verified=auth.user.email_verified_at is not None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch("/me", response_model=ProfileResponse)
async def patch_me(
    body: ProfileUpdate,
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> ProfileResponse:
    """Update explicitly provided profile fields."""
    fields = body.model_fields_set
    updated = await update_profile(
        accounts=repos.accounts,
        user_id=auth.user.id,
        display_name=body.display_name if "display_name" in fields else None,
        locale=body.locale if "locale" in fields else None,
        timezone=body.timezone if "timezone" in fields else None,
    )
    return ProfileResponse(
        id=auth.user.id,
        email=auth.user.email,
        display_name=updated["display_name"],
        locale=updated["locale"],
        timezone=updated["timezone"],
        status=auth.user.status.value,
        email_verified=auth.user.email_verified_at is not None,
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )


@router.get("/me/entitlements", response_model=EntitlementView)
async def entitlements(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> EntitlementView:
    """Return the backend-calculated plan, permissions and quota."""
    return await evaluate_entitlement(
        user=auth.user,
        session=auth.session,
        plan_repo=repos.plans,
        subscription_repo=repos.subscriptions,
        usage_repo=repos.usage,
        now=utcnow(),
    )


@router.get("/me/usage", response_model=UsageResponse)
async def usage(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> UsageResponse:
    """Expose only the caller's consumption and limits."""
    view = await evaluate_entitlement(
        user=auth.user,
        session=auth.session,
        plan_repo=repos.plans,
        subscription_repo=repos.subscriptions,
        usage_repo=repos.usage,
        now=utcnow(),
    )
    return UsageResponse(
        plan_code=view.plan_code,
        quotas=view.quotas,
        remaining=view.quota_remaining,
    )


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_me(
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
    container: Container = Depends(get_container),
) -> dict[str, str]:
    """Revoke sessions immediately and schedule account purge."""
    await request_account_deletion(
        accounts=repos.accounts,
        sessions=repos.sessions,
        security=repos.security,
        user_id=auth.user.id,
        authenticated_at=auth.access.issued_at,
        grace_days=container.settings.account_deletion_grace_days,
    )
    return {"status": "deletion_scheduled"}
