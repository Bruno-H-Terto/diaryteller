"""Speech transport contracts for transcription and synthesis.

Audio bytes never appear in these models; they travel as binary request/response
bodies with strict byte limits.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AudioFormat(StrEnum):
    """Formats accepted or produced by the configured provider."""

    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    OGG = "ogg"
    WEBM = "webm"


class TranscriptionResponse(BaseModel):
    """Transcription metadata and text owned by the phone after the response."""

    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    text: str
    language: str | None = None
    duration_seconds: float = Field(ge=0)
    provider_format: AudioFormat


class Voice(BaseModel):
    """One provider-authorized voice; cloning is not supported."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str | None = None


class VoiceCatalog(BaseModel):
    """Voices the account may select."""

    model_config = ConfigDict(extra="forbid")

    voices: list[Voice]


class SynthesisRequest(BaseModel):
    """Text and voice for TTS. The text is not stored."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    voice_id: str = Field(min_length=1, max_length=64)
    format: AudioFormat = AudioFormat.MP3
    locale: str | None = Field(default=None, max_length=16)
