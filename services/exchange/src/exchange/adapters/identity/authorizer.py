"""HTTP adapter for the identity service's authoritative decision."""

from __future__ import annotations

import httpx
from diary_contracts.authorization import (
    AccountStatus,
    AuthorizeDecision,
    AuthorizeRequest,
    Permission,
)
from diary_contracts.errors import DomainError, ErrorCode

from exchange.application.ports.identity import Principal

REASON_ERRORS = {
    "email_not_verified": (ErrorCode.EMAIL_NOT_VERIFIED, 403, "Email verification is required"),
    "account_disabled": (ErrorCode.ACCOUNT_DISABLED, 403, "Account is not active"),
    "permission_missing": (ErrorCode.FORBIDDEN, 403, "Permission is missing"),
}


class IdentityHttpAuthorizer:
    """Validate the caller with the identity service, never locally."""

    def __init__(
        self,
        *,
        base_url: str,
        service: str,
        token: str,
        http: httpx.AsyncClient,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service = service
        self._token = token
        self._http = http

    async def authorize(self, *, authorization: str, source: str, permission: str) -> Principal:
        """Return the principal or raise the mapped domain error."""
        payload = AuthorizeRequest(permission=Permission(permission))
        try:
            response = await self._http.post(
                f"{self._base_url}/internal/authorize",
                json=payload.model_dump(mode="json"),
                headers={
                    "Authorization": authorization,
                    "X-Session-Source": source,
                    "X-Internal-Service": self._service,
                    "X-Internal-Token": self._token,
                },
            )
        except httpx.HTTPError as exc:
            raise DomainError(
                ErrorCode.PROVIDER_UNAVAILABLE, 503, "Identity service is unavailable"
            ) from exc
        if response.status_code >= 500:
            raise DomainError(
                ErrorCode.PROVIDER_UNAVAILABLE, 503, "Identity service is unavailable"
            )
        if response.status_code != 200:
            raise _error_from(response)
        decision = AuthorizeDecision.model_validate(response.json())
        if not decision.allowed:
            raise _reason_error(decision.reason)
        entitlement = decision.entitlement
        return Principal(
            user_id=entitlement.user_id,
            session_id=entitlement.session_id,
            account_status=AccountStatus(entitlement.account_status),
            plan_code=entitlement.plan_code,
        )


def _error_from(response: httpx.Response) -> DomainError:
    try:
        body = response.json()
    except ValueError:
        body = {}
    code = body.get("code") if isinstance(body, dict) else None
    try:
        error_code = ErrorCode(code) if code else ErrorCode.AUTH_INVALID
    except ValueError:
        error_code = ErrorCode.AUTH_INVALID
    status = response.status_code if 400 <= response.status_code < 500 else 401
    return DomainError(error_code, status, "Caller is not authorized")


def _reason_error(reason: str | None) -> DomainError:
    code, status, message = REASON_ERRORS.get(reason or "", (ErrorCode.FORBIDDEN, 403, "Forbidden"))
    return DomainError(code, status, message)
