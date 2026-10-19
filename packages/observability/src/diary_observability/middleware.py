"""Request identity, no-store responses and the standard error envelope.

Handlers raise `DomainError`; this module maps it to a safe JSON body. Unexpected
errors never expose exception text, provider payloads or stack traces.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from contextvars import ContextVar

from diary_contracts.errors import DomainError, ErrorCode, ErrorEnvelope, error_type
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_logger = logging.getLogger("request")


def current_request_id() -> str:
    """Return the current request identifier or a fresh one."""
    return REQUEST_ID.get() or str(uuid.uuid4())


async def request_context(request: Request, call_next):
    """Attach a request id and forbid caching of any response."""
    incoming = request.headers.get("X-Request-ID", "")
    request_id = incoming if _REQUEST_ID_PATTERN.match(incoming) else str(uuid.uuid4())
    token = REQUEST_ID.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        REQUEST_ID.reset(token)
    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("Cache-Control", "no-store")
    _logger.info(
        "http_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path[:128],
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


def envelope(
    *,
    status: int,
    code: ErrorCode,
    title: str,
    retryable: bool = False,
    details: dict | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build the documented JSON error response."""
    body = ErrorEnvelope(
        type=error_type(code),
        title=title,
        message=title,
        status=status,
        code=code,
        request_id=request_id or current_request_id(),
        retryable=retryable,
        details=details or {},
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=status)


_HTTP_CODES = {
    401: (ErrorCode.AUTH_INVALID, "Authentication required", False),
    403: (ErrorCode.FORBIDDEN, "Access denied", False),
    404: (ErrorCode.NOT_FOUND, "Resource not found", False),
    409: (ErrorCode.IDEMPOTENCY_CONFLICT, "Request conflicts with current state", False),
    413: (ErrorCode.MEDIA_TOO_LARGE, "Payload too large", False),
    415: (ErrorCode.MEDIA_INVALID, "Unsupported media type", False),
    422: (ErrorCode.VALIDATION_ERROR, "Invalid request", False),
    429: (ErrorCode.RATE_LIMITED, "Too many requests", True),
    502: (ErrorCode.PROVIDER_UNAVAILABLE, "Upstream provider unavailable", True),
    503: (ErrorCode.PROVIDER_UNAVAILABLE, "Service temporarily unavailable", True),
    504: (ErrorCode.PROVIDER_TIMEOUT, "Upstream provider timed out", True),
}


def install_error_handlers(app: FastAPI) -> None:
    """Register domain, validation, HTTP and catch-all handlers."""

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return envelope(
            status=exc.status,
            code=exc.code,
            title=exc.title,
            retryable=exc.retryable,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {"location": ".".join(str(part) for part in error.get("loc", ()))[:120]}
            for error in exc.errors()[:10]
        ]
        return envelope(
            status=422,
            code=ErrorCode.VALIDATION_ERROR,
            title="Invalid request",
            details={"fields": fields},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, title, retryable = _HTTP_CODES.get(
            exc.status_code, (ErrorCode.INTERNAL_ERROR, "Request failed", False)
        )
        return envelope(status=exc.status_code, code=code, title=title, retryable=retryable)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        _logger.error(
            "unexpected_error",
            extra={"request_id": current_request_id(), "error_code": type(exc).__name__[:64]},
        )
        return envelope(
            status=500,
            code=ErrorCode.INTERNAL_ERROR,
            title="Internal server error",
        )
