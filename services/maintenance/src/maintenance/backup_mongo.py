"""Encrypted MongoDB backups using the native mongodump tool."""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from maintenance.backup_encrypt import encrypt_file
from maintenance.backup_postgres import prune
from maintenance.settings import MaintenanceSettings


def _dump(settings: MaintenanceSettings, target: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as config:
        config.write(f"uri: {settings.mongo_url}\n")
        config_path = Path(config.name)
    config_path.chmod(0o600)
    try:
        result = subprocess.run(
            [
                settings.mongodump_binary,
                "--config",
                str(config_path),
                f"--archive={target}",
                "--gzip",
            ],
            capture_output=True,
            timeout=settings.backup_timeout_seconds,
            check=False,
            env=os.environ,
        )
        if result.returncode != 0:
            raise RuntimeError("mongodump failed")
    finally:
        config_path.unlink(missing_ok=True)


async def backup_mongo(settings: MaintenanceSettings) -> Path:
    """Create an encrypted archive of sanitized operational logs only."""
    directory = Path(settings.backup_dir)
    directory.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240 - tiny local ops
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    plain = directory / f".mongo-{stamp}.archive"
    encrypted = directory / f"mongo-{stamp}.archive.enc"
    try:
        await asyncio.to_thread(_dump, settings, plain)
        checksum = await asyncio.to_thread(
            encrypt_file, plain, encrypted, settings.backup_encryption_key
        )
        sidecar = encrypted.with_suffix(encrypted.suffix + ".sha256")
        sidecar.write_text(f"{checksum}  {encrypted.name}\n", encoding="utf-8")
        sidecar.chmod(0o600)
        await asyncio.to_thread(prune, settings, "mongo-")
    finally:
        if plain.exists():
            plain.unlink()
    return encrypted
