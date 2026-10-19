"""OpenAI transcription and TTS adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal

from diary_contracts.speech import AudioFormat, Voice
from openai import AsyncOpenAI
from speech.lib.ports import Transcription

ProviderFormat = Literal["mp3", "wav", "opus"]
_OPENAI_FORMATS: dict[AudioFormat, ProviderFormat] = {
    AudioFormat.MP3: "mp3",
    AudioFormat.WAV: "wav",
    AudioFormat.OGG: "opus",
}


class OpenAISpeechProvider:
    """Provider-bound speech operations with bounded output."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        stt_model: str,
        tts_model: str,
        timeout_seconds: float,
        voices: list[str],
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=0,
        )
        self._stt_model = stt_model
        self._tts_model = tts_model
        self._voices = voices

    async def transcribe(
        self, data: bytes, filename: str, content_type: str, language: str | None
    ) -> Transcription:
        """Transcribe audio without persisting it."""
        request = {
            "file": (filename, data, content_type),
            "model": self._stt_model,
            "response_format": "json",
        }
        if language:
            request["language"] = language
        response = await self._client.audio.transcriptions.create(**request)
        return Transcription(text=response.text, language=language)

    def synthesize(self, text: str, voice: str, audio_format: AudioFormat) -> AsyncIterator[bytes]:
        """Return an async iterator over provider audio bytes."""
        if voice not in self._voices:
            raise ValueError("voice is not allowed")
        provider_format = _OPENAI_FORMATS.get(audio_format)
        if provider_format is None:
            raise ValueError("format is not supported for synthesis")
        return self._stream(text, voice, provider_format)

    async def _stream(
        self, text: str, voice: str, provider_format: ProviderFormat
    ) -> AsyncIterator[bytes]:
        response = await self._client.audio.speech.create(
            input=text,
            model=self._tts_model,
            voice=voice,
            response_format=provider_format,
            stream_format="audio",
        )
        iterator = await response.aiter_bytes()
        async for chunk in iterator:
            if chunk:
                yield chunk

    def voices(self) -> list[Voice]:
        """Configured provider voices; no cloning."""
        return [
            Voice(id=voice, name=voice.capitalize(), description="Provider voice")
            for voice in self._voices
        ]
