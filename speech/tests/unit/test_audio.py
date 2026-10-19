"""Audio validation tests."""

from __future__ import annotations

import struct

import pytest
from diary_contracts.speech import AudioFormat
from speech.models.audio import MediaInvalid, detect_format, validate_audio, wav_duration


def wav(seconds: float, sample_rate: int = 8000) -> bytes:
    payload = b"\x00\x00" * int(seconds * sample_rate)
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(payload))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(payload))
        + payload
    )


def test_detect_and_duration() -> None:
    data = wav(1.5)
    assert detect_format(data) is AudioFormat.WAV
    assert wav_duration(data) == pytest.approx(1.5)


async def test_validate_bounds() -> None:
    info = await validate_audio(
        wav(1),
        AudioFormat.WAV,
        max_bytes=1024 * 1024,
        max_seconds=120,
        ffprobe_binary="ffprobe",
        probe_timeout=2,
    )
    assert info.duration_seconds == 1.0
    with pytest.raises(MediaInvalid):
        await validate_audio(
            wav(2),
            AudioFormat.WAV,
            max_bytes=1024 * 1024,
            max_seconds=1,
            ffprobe_binary="ffprobe",
            probe_timeout=2,
        )


def test_wrong_declared_format_rejected() -> None:
    with pytest.raises(MediaInvalid):
        import asyncio

        asyncio.run(
            validate_audio(
                wav(1),
                AudioFormat.MP3,
                max_bytes=1024 * 1024,
                max_seconds=120,
                ffprobe_binary="ffprobe",
                probe_timeout=2,
            )
        )
