"""Deterministic speech provider for tests and explicit local development."""

from __future__ import annotations

import math
import struct
from collections.abc import AsyncIterator

from diary_contracts.speech import AudioFormat, Voice
from speech.lib.ports import Transcription


class FakeSpeechProvider:
    """Produce deterministic text and silent audio."""

    def __init__(self, voices: list[str]) -> None:
        self._voices = voices

    async def transcribe(
        self, data: bytes, filename: str, content_type: str, language: str | None
    ) -> Transcription:
        """Return a fixed transcription marker."""
        return Transcription(
            text=f"Transcrição sintética de {len(data)} bytes.",
            language=language or "pt",
        )

    def synthesize(self, text: str, voice: str, audio_format: AudioFormat) -> AsyncIterator[bytes]:
        """Yield a small WAV or MP3-prefixed payload based on requested format."""
        if voice not in self._voices:
            raise ValueError("voice is not allowed")
        return self._stream(text, audio_format)

    async def _stream(self, text: str, audio_format: AudioFormat) -> AsyncIterator[bytes]:
        seconds = min(5.0, math.ceil(len(text) / 15))
        if audio_format is AudioFormat.WAV:
            sample_rate = 8000
            frames = int(seconds * sample_rate)
            payload = b"\x00\x00" * frames
            header = b"RIFF" + struct.pack("<I", 36 + len(payload)) + b"WAVE"
            fmt = b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
            data = b"data" + struct.pack("<I", len(payload))
            yield header + fmt + data + payload
            return
        yield b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * min(4096, len(text) * 4)

    def voices(self) -> list[Voice]:
        """Configured voices."""
        return [
            Voice(id=voice, name=voice.capitalize(), description="Synthetic provider voice")
            for voice in self._voices
        ]
