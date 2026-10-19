"""Request helpers shared by speech routes."""

from __future__ import annotations

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.speech import AudioFormat
from fastapi import Request

from speech.application.ports import AuthHeaders


def auth_headers(authorization: str, source: str) -> AuthHeaders:
    """Require user credentials forwarded to identity."""
    if not authorization.lower().startswith("bearer ") or not source:
        raise DomainError(ErrorCode.AUTH_INVALID, 401, "Authentication required")
    return AuthHeaders(authorization=authorization, source=source)


def require_idempotency(value: str) -> str:
    """Validate the idempotency header."""
    if not 8 <= len(value) <= 128:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, 422, "A valid Idempotency-Key header is required"
        )
    return value


async def read_limited(request: Request, max_bytes: int) -> bytes:
    """Stream the binary body with a hard byte limit."""
    declared = int(request.headers.get("content-length", "0") or 0)
    if declared > max_bytes:
        raise DomainError(ErrorCode.MEDIA_TOO_LARGE, 413, "Audio exceeds the byte limit")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > max_bytes:
            raise DomainError(ErrorCode.MEDIA_TOO_LARGE, 413, "Audio exceeds the byte limit")
        data.extend(chunk)
    return bytes(data)


def declared_format(value: str | None, content_type: str) -> AudioFormat | None:
    """Parse an explicit format header or map a supported MIME type."""
    if value:
        try:
            return AudioFormat(value.lower())
        except ValueError as exc:
            raise DomainError(ErrorCode.MEDIA_INVALID, 415, "Unsupported audio format") from exc
    mapping = {
        "audio/wav": AudioFormat.WAV,
        "audio/x-wav": AudioFormat.WAV,
        "audio/mpeg": AudioFormat.MP3,
        "audio/mp3": AudioFormat.MP3,
        "audio/mp4": AudioFormat.M4A,
        "audio/x-m4a": AudioFormat.M4A,
        "audio/ogg": AudioFormat.OGG,
        "audio/webm": AudioFormat.WEBM,
    }
    return mapping.get(content_type.split(";", 1)[0].strip().lower())
