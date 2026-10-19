"""Explicitly assembled speech dependencies."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from diary_observability import MongoLogSink

from speech.adapters.identity.client import IdentityClient
from speech.adapters.provider.fake import FakeSpeechProvider
from speech.adapters.provider.openai import OpenAISpeechProvider
from speech.application.ports import SpeechProvider
from speech.settings import Settings


@dataclass(slots=True)
class Container:
    """Runtime objects shared by speech requests."""

    settings: Settings
    identity_http: httpx.AsyncClient
    identity: IdentityClient
    provider: SpeechProvider
    sink: MongoLogSink


def build_provider(settings: Settings) -> SpeechProvider:
    """Select OpenAI or the explicit local fake."""
    if settings.speech_provider == "openai":
        return OpenAISpeechProvider(
            settings.openai_api_key,
            settings.openai_base_url,
            settings.stt_model,
            settings.tts_model,
            settings.provider_timeout_seconds,
            settings.voices,
        )
    return FakeSpeechProvider(settings.voices)
