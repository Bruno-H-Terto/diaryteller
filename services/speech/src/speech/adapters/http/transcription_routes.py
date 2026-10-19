"""Bounded audio transcription endpoint."""

from __future__ import annotations

import contextlib
import math

from diary_contracts.authorization import Permission, UsageMetric
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import OperationState, OperationType
from diary_contracts.speech import TranscriptionResponse
from diary_security import hmac_digest, sha256_bytes
from fastapi import APIRouter, Header, Request

from speech.adapters.http.common import (
    auth_headers,
    declared_format,
    read_limited,
    require_idempotency,
)
from speech.application.operations import finish, prepare
from speech.container import Container
from speech.domain.audio import MediaInvalid, validate_audio

router = APIRouter(prefix="/speech", tags=["speech"])


def _container(request: Request) -> Container:
    return request.app.state.container


@router.post("/transcriptions", response_model=TranscriptionResponse)
async def transcribe(
    request: Request,
    authorization: str = Header(default=""),
    x_session_source: str = Header(default="", alias="X-Session-Source"),
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    x_audio_format: str | None = Header(default=None, alias="X-Audio-Format"),
    x_audio_language: str | None = Header(default=None, alias="X-Audio-Language"),
) -> TranscriptionResponse:
    """Transcribe audio without persisting or logging its bytes."""
    container = _container(request)
    settings = container.settings
    auth = auth_headers(authorization, x_session_source)
    key = require_idempotency(idempotency_key)
    language = (x_audio_language or "").strip()[:16] or None
    data = await read_limited(request, settings.max_audio_bytes)
    try:
        info = await validate_audio(
            data,
            declared_format(x_audio_format, request.headers.get("content-type", "")),
            max_bytes=settings.max_audio_bytes,
            max_seconds=settings.max_audio_seconds,
            ffprobe_binary=settings.ffprobe_binary,
            probe_timeout=settings.ffprobe_timeout_seconds,
        )
    except MediaInvalid as exc:
        raise DomainError(ErrorCode.MEDIA_INVALID, 415, str(exc)) from exc
    estimated = max(1, math.ceil(info.duration_seconds))
    digest = hmac_digest(
        settings.idempotency_hmac_key,
        {"kind": "transcription", "sha256": sha256_bytes(data), "format": info.format.value},
    )
    operation = await prepare(
        identity=container.identity,
        auth=auth,
        permission=Permission.SPEECH_TRANSCRIBE,
        operation_type=OperationType.TRANSCRIPTION,
        metric=UsageMetric.SPEECH_SECONDS,
        estimated=estimated,
        idempotency_key=key,
        payload_digest=digest,
    )
    try:
        result = await container.provider.transcribe(
            data,
            f"audio.{info.format.value}",
            request.headers.get("content-type", "application/octet-stream"),
            language,
        )
    except Exception as exc:
        with contextlib.suppress(Exception):
            await finish(
                identity=container.identity,
                auth=auth,
                operation_id=operation.operation_id,
                state=OperationState.FAILED,
                actual=None,
                error_code="provider_unavailable",
            )
        raise DomainError(
            ErrorCode.PROVIDER_UNAVAILABLE, 502, "Transcription provider failed", retryable=True
        ) from exc
    with contextlib.suppress(Exception):
        await finish(
            identity=container.identity,
            auth=auth,
            operation_id=operation.operation_id,
            state=OperationState.SUCCEEDED,
            actual=estimated,
            error_code=None,
        )
    return TranscriptionResponse(
        operation_id=operation.operation_id,
        text=result.text,
        language=result.language,
        duration_seconds=info.duration_seconds,
        provider_format=info.format,
    )
