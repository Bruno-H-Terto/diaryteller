"""HTTP client for identity internal authorization, quota and control routes."""

from __future__ import annotations

import contextlib
from typing import Any
from uuid import UUID

import httpx
from conversation.lib.ports import AuthHeaders
from diary_contracts.authorization import AuthorizeDecision, Permission, UsageMetric
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import (
    FinishRequest,
    OperationControl,
    OperationView,
    ReserveRequest,
    ReserveResult,
)


class IdentityClient:
    """Forward user credentials plus a service credential to identity."""

    def __init__(self, http: httpx.AsyncClient, base_url: str, service_token: str) -> None:
        self._http = http
        self._base = base_url.rstrip("/")
        self._token = service_token

    def _headers(self, auth: AuthHeaders) -> dict[str, str]:
        return {
            "Authorization": auth.authorization,
            "X-Session-Source": auth.source,
            "X-Internal-Service": "conversation",
            "X-Internal-Token": self._token,
        }

    async def _request(
        self, method: str, path: str, auth: AuthHeaders, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = await self._http.request(
                method,
                f"{self._base}{path}",
                headers=self._headers(auth),
                json=body,
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
            data = {}
            with contextlib.suppress(ValueError):
                data = response.json()
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
        """Call `/internal/authorize`."""
        data = await self._request(
            "POST", "/internal/authorize", headers, {"permission": permission.value}
        )
        return AuthorizeDecision.model_validate(data)

    async def reserve(self, headers: AuthHeaders, request: ReserveRequest) -> ReserveResult:
        """Call `/internal/operations/reserve`."""
        data = await self._request(
            "POST",
            "/internal/operations/reserve",
            headers,
            request.model_dump(mode="json"),
        )
        return ReserveResult.model_validate(data)

    async def finish(
        self, headers: AuthHeaders, operation_id: UUID, request: FinishRequest
    ) -> OperationView:
        """Call the finish callback idempotently."""
        data = await self._request(
            "POST",
            f"/internal/operations/{operation_id}/finish",
            headers,
            request.model_dump(mode="json"),
        )
        return OperationView.model_validate(data)

    async def control(self, headers: AuthHeaders, operation_id: UUID) -> OperationControl:
        """Fetch cancellation/session control state."""
        data = await self._request("GET", f"/internal/operations/{operation_id}/control", headers)
        return OperationControl.model_validate(data)

    async def consume(self, headers: AuthHeaders, metric: UsageMetric, amount: int) -> None:
        """Consume incremental metered usage (memory calls)."""
        await self._request(
            "POST",
            "/internal/usage/consume",
            headers,
            {"metric": metric.value, "amount": amount},
        )
