"""HTTP client for identity internal routes used by speech."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from diary_contracts.authorization import AuthorizeDecision, Permission
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import (
    FinishRequest,
    OperationView,
    ReserveRequest,
    ReserveResult,
)

from speech.application.ports import AuthHeaders


class IdentityClient:
    """Forward user credentials with the speech service credential."""

    def __init__(self, http: httpx.AsyncClient, base_url: str, service_token: str) -> None:
        self._http = http
        self._base = base_url.rstrip("/")
        self._token = service_token

    def _headers(self, auth: AuthHeaders) -> dict[str, str]:
        return {
            "Authorization": auth.authorization,
            "X-Session-Source": auth.source,
            "X-Internal-Service": "speech",
            "X-Internal-Token": self._token,
        }

    async def _request(
        self, method: str, path: str, auth: AuthHeaders, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = await self._http.request(
                method, f"{self._base}{path}", headers=self._headers(auth), json=body
            )
        except httpx.TimeoutException as exc:
            raise DomainError(
                ErrorCode.PROVIDER_TIMEOUT, 504, "Identity timed out", retryable=True
            ) from exc
        except httpx.HTTPError as exc:
            raise DomainError(
                ErrorCode.PROVIDER_UNAVAILABLE, 503, "Identity unavailable", retryable=True
            ) from exc
        if response.status_code >= 400:
            try:
                data = response.json()
            except ValueError:
                data = {}
            try:
                code = ErrorCode(data.get("code", ErrorCode.INTERNAL_ERROR.value))
            except ValueError:
                code = ErrorCode.INTERNAL_ERROR
            raise DomainError(
                code,
                response.status_code,
                str(data.get("title", "Identity request failed")),
                retryable=bool(data.get("retryable", False)),
                details=data.get("details") or {},
            )
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    async def authorize(self, headers: AuthHeaders, permission: Permission) -> AuthorizeDecision:
        """Authorize one permission."""
        return AuthorizeDecision.model_validate(
            await self._request(
                "POST", "/internal/authorize", headers, {"permission": permission.value}
            )
        )

    async def reserve(self, headers: AuthHeaders, request: ReserveRequest) -> ReserveResult:
        """Reserve operation quota."""
        return ReserveResult.model_validate(
            await self._request(
                "POST",
                "/internal/operations/reserve",
                headers,
                request.model_dump(mode="json"),
            )
        )

    async def finish(
        self, headers: AuthHeaders, operation_id: UUID, request: FinishRequest
    ) -> OperationView:
        """Finalize consumption."""
        return OperationView.model_validate(
            await self._request(
                "POST",
                f"/internal/operations/{operation_id}/finish",
                headers,
                request.model_dump(mode="json"),
            )
        )
