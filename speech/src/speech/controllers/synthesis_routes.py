"""Voice catalog and streaming text-to-speech endpoints."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
from collections.abc import AsyncIterator
from math import ceil

from diary_contracts.authorization import Permission, UsageMetric
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import OperationState, OperationType
from diary_contracts.speech import AudioFormat, SynthesisRequest, VoiceCatalog
from diary_security import hmac_digest
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from speech.config.container import Container
from speech.controllers.common import auth_headers, require_idempotency
from speech.services.operations import finish, prepare

router = APIRouter(prefix="/speech", tags=["speech"])
_logger = logging.getLogger(__name__)

_MEDIA_TYPES = {
    AudioFormat.MP3: "audio/mpeg",
    AudioFormat.WAV: "audio/wav",
    AudioFormat.OGG: "audio/ogg",
}


def _container(request: Request) -> Container:
    return request.app.state.container


def _best_effort(container: Container, auth, operation_id, state, code) -> None:
    async def run() -> None:
        with contextlib.suppress(Exception):
            await finish(
                identity=container.identity,
                auth=auth,
                operation_id=operation_id,
                state=state,
                actual=None,
                error_code=code,
            )

    task = asyncio.create_task(run())
    task.add_done_callback(lambda value: value.exception() if value.done() else None)


@router.get("/voices", response_model=VoiceCatalog)
async def voices(
    request: Request,
    authorization: str = Header(default=""),
    x_session_source: str = Header(default="", alias="X-Session-Source"),
) -> VoiceCatalog:
    """Return the provider-authorized catalog."""
    container = _container(request)
    auth = auth_headers(authorization, x_session_source)
    decision = await container.identity.authorize(auth, Permission.SPEECH_SYNTHESIZE)
    if not decision.allowed:
        raise DomainError(
            ErrorCode.SUBSCRIPTION_REQUIRED, 403, "Plan does not allow speech synthesis"
        )
    return VoiceCatalog(voices=container.provider.voices())


@router.post("/syntheses")
async def synthesize(
    body: SynthesisRequest,
    request: Request,
    authorization: str = Header(default=""),
    x_session_source: str = Header(default="", alias="X-Session-Source"),
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
) -> StreamingResponse:
    """Stream synthesized audio; the text is not stored."""
    container = _container(request)
    settings = container.settings
    auth = auth_headers(authorization, x_session_source)
    key = require_idempotency(idempotency_key)
    if body.voice_id not in settings.voices:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Voice is not allowed")
    if body.format not in _MEDIA_TYPES:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Unsupported synthesis format")
    if len(body.text) > settings.tts_max_chars:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Text exceeds the synthesis limit")
    estimated = max(1, min(settings.max_audio_seconds, ceil(len(body.text) / 15)))
    digest = hmac_digest(
        settings.idempotency_hmac_key,
        {
            "kind": "synthesis",
            "text_sha256": hashlib.sha256(body.text.encode()).hexdigest(),
            "voice": body.voice_id,
            "format": body.format.value,
        },
    )
    operation = await prepare(
        identity=container.identity,
        auth=auth,
        permission=Permission.SPEECH_SYNTHESIZE,
        operation_type=OperationType.SYNTHESIS,
        metric=UsageMetric.SPEECH_SECONDS,
        estimated=estimated,
        idempotency_key=key,
        payload_digest=digest,
    )
    try:
        chunks = container.provider.synthesize(body.text, body.voice_id, body.format)
    except ValueError as exc:
        with contextlib.suppress(Exception):
            await finish(
                identity=container.identity,
                auth=auth,
                operation_id=operation.operation_id,
                state=OperationState.FAILED,
                actual=0,
                error_code="invalid_request",
            )
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Synthesis request rejected") from exc

    async def stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in chunks:
                yield chunk
            await finish(
                identity=container.identity,
                auth=auth,
                operation_id=operation.operation_id,
                state=OperationState.SUCCEEDED,
                actual=estimated,
                error_code=None,
            )
        except asyncio.CancelledError:
            _best_effort(
                container, auth, operation.operation_id, OperationState.INTERRUPTED, "interrupted"
            )
            raise
        except Exception:
            _logger.warning(
                "synthesis_failed",
                extra={"operation_id": str(operation.operation_id), "error_code": "provider"},
            )
            _best_effort(
                container,
                auth,
                operation.operation_id,
                OperationState.FAILED,
                "provider_unavailable",
            )

    return StreamingResponse(
        stream(),
        media_type=_MEDIA_TYPES[body.format],
        headers={
            "X-Operation-Id": str(operation.operation_id),
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )
