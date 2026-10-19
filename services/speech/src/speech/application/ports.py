"""Speech provider and identity ports."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from diary_contracts.authorization import AuthorizeDecision, Permission
from diary_contracts.operation import (
    FinishRequest,
    OperationView,
    ReserveRequest,
    ReserveResult,
)
from diary_contracts.speech import AudioFormat, Voice


@dataclass(frozen=True, slots=True)
class AuthHeaders:
    """Inbound user credentials forwarded to identity."""

    authorization: str
    source: str


@dataclass(frozen=True, slots=True)
class Transcription:
    """Provider transcription text and detected language."""

    text: str
    language: str | None


class SpeechProvider(Protocol):
    """Replaceable transcription and TTS boundary."""

    async def transcribe(
        self,
        data: bytes,
        filename: str,
        content_type: str,
        language: str | None,
    ) -> Transcription:
        """Transcribe bounded audio bytes."""
        ...

    def synthesize(self, text: str, voice: str, audio_format: AudioFormat) -> AsyncIterator[bytes]:
        """Stream synthesized audio bytes."""
        ...

    def voices(self) -> list[Voice]:
        """Return the provider-authorized voice catalog."""
        ...


class IdentityPort(Protocol):
    """Identity authorization, reservation and finalization."""

    async def authorize(self, headers: AuthHeaders, permission: Permission) -> AuthorizeDecision:
        """Return the current decision."""
        ...

    async def reserve(self, headers: AuthHeaders, request: ReserveRequest) -> ReserveResult:
        """Reserve quota."""
        ...

    async def finish(
        self, headers: AuthHeaders, operation_id: UUID, request: FinishRequest
    ) -> OperationView:
        """Finalize consumption."""
        ...
