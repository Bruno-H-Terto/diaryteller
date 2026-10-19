"""Binary audio limits, format detection and duration validation.

The declared MIME type is never trusted alone. WAV duration is parsed locally;
other formats are probed in a bounded subprocess and the temporary file is
always removed.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import resource
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from diary_contracts.speech import AudioFormat

_TEMP_DIR = "/dev/shm" if os.path.isdir("/dev/shm") else None


class MediaInvalid(Exception):
    """The uploaded bytes are not a supported, bounded audio file."""


@dataclass(frozen=True, slots=True)
class AudioInfo:
    """Validated format and duration."""

    format: AudioFormat
    duration_seconds: float


def detect_format(data: bytes) -> AudioFormat | None:
    """Detect format from magic bytes, not from extension or MIME."""
    if len(data) < 12:
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return AudioFormat.WAV
    if data[:4] == b"OggS":
        return AudioFormat.OGG
    if data[:4] == b"\x1aE\xdf\xa3":
        return AudioFormat.WEBM
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in {b"M4A ", b"M4B ", b"mp42", b"isom"}:
            return AudioFormat.M4A
    if data[:3] == b"ID3" or (data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return AudioFormat.MP3
    return None


def wav_duration(data: bytes) -> float:
    """Parse the WAV fmt/data chunks for duration."""
    offset = 12
    byte_rate = 0
    data_size = 0
    while offset + 8 <= len(data):
        chunk_id = data[offset : offset + 4]
        size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
        body = offset + 8
        if chunk_id == b"fmt " and size >= 16 and body + 16 <= len(data):
            byte_rate = struct.unpack("<I", data[body + 8 : body + 12])[0]
        elif chunk_id == b"data":
            data_size = min(size, len(data) - body)
            break
        offset = body + size + (size % 2)
    if byte_rate <= 0 or data_size <= 0:
        raise MediaInvalid("invalid wav header")
    return data_size / byte_rate


def _probe_limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))


def _probe_sync(path: str, binary: str, timeout: float) -> float:
    result = subprocess.run(
        [
            binary,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True,
        timeout=timeout,
        check=False,
        preexec_fn=_probe_limits,
    )
    if result.returncode != 0:
        raise MediaInvalid("audio probe failed")
    try:
        return float(result.stdout.decode().strip())
    except ValueError as exc:
        raise MediaInvalid("audio duration unknown") from exc


async def validate_audio(
    data: bytes,
    declared: AudioFormat | None,
    *,
    max_bytes: int,
    max_seconds: int,
    ffprobe_binary: str,
    probe_timeout: float,
) -> AudioInfo:
    """Validate size, format and duration."""
    if not data or len(data) > max_bytes:
        raise MediaInvalid("audio size is invalid")
    detected = detect_format(data)
    if detected is None:
        raise MediaInvalid("unsupported audio format")
    if declared is not None and declared is not detected:
        raise MediaInvalid("declared format does not match content")
    if detected is AudioFormat.WAV:
        duration = wav_duration(data)
    else:
        suffix = f".{detected.value}"
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - path needed after close
            suffix=suffix, dir=_TEMP_DIR, delete=False
        )
        path = Path(handle.name)
        try:
            with handle:
                handle.write(data)
            duration = await asyncio.to_thread(
                _probe_sync, str(path), ffprobe_binary, probe_timeout
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise MediaInvalid("audio probe unavailable") from exc
        finally:
            with contextlib.suppress(OSError):
                path.unlink()  # noqa: ASYNC240 - bounded cleanup
    if duration <= 0 or duration > max_seconds:
        raise MediaInvalid("audio duration is out of bounds")
    return AudioInfo(format=detected, duration_seconds=round(duration, 3))
