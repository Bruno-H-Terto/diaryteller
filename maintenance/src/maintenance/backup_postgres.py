"""Encrypted logical PostgreSQL backups without diary content."""

from __future__ import annotations

import asyncio
import hashlib
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from maintenance.backup_encrypt import encrypt_file
from maintenance.settings import MaintenanceSettings


def _connection(settings: MaintenanceSettings) -> tuple[dict[str, str], list[str]]:
    url = urlparse(settings.database_url.replace("+asyncpg", ""))
    env = {
        "PGHOST": url.hostname or "localhost",
        "PGPORT": str(url.port or 5432),
        "PGUSER": unquote(url.username or "diary"),
        "PGPASSWORD": unquote(url.password or ""),
        "PGDATABASE": url.path.lstrip("/") or "diary",
    }
    return env, [settings.pg_dump_binary, "--format=custom", "--no-owner", "--no-acl"]


def _dump(settings: MaintenanceSettings, target: Path) -> None:
    env, command = _connection(settings)
    environment = {**os.environ, **env}
    result = subprocess.run(
        [*command, "--file", str(target)],
        capture_output=True,
        timeout=settings.backup_timeout_seconds,
        check=False,
        env=environment,
    )
    if result.returncode != 0:
        raise RuntimeError("pg_dump failed")


def prune(settings: MaintenanceSettings, prefix: str) -> int:
    """Remove encrypted backups older than retention."""
    cutoff = datetime.now(UTC) - timedelta(days=settings.backup_retention_days)
    directory = Path(settings.backup_dir)
    removed = 0
    for path in directory.glob(f"{prefix}*.enc"):
        if datetime.fromtimestamp(path.stat().st_mtime, UTC) < cutoff:
            path.unlink(missing_ok=True)
            path.with_suffix(path.suffix + ".sha256").unlink(missing_ok=True)
            removed += 1
    return removed


async def backup_postgres(settings: MaintenanceSettings) -> Path:
    """Create, encrypt, checksum and prune an administrative dump."""
    directory = Path(settings.backup_dir)
    directory.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240 - tiny local ops
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    plain = directory / f".postgres-{stamp}.dump"
    encrypted = directory / f"postgres-{stamp}.dump.enc"
    try:
        await asyncio.to_thread(_dump, settings, plain)
        checksum = await asyncio.to_thread(
            encrypt_file, plain, encrypted, settings.backup_encryption_key
        )
        encrypted.with_suffix(encrypted.suffix + ".sha256").write_text(
            f"{checksum}  {encrypted.name}\n", encoding="utf-8"
        )
        encrypted.with_suffix(encrypted.suffix + ".sha256").chmod(0o600)
        await asyncio.to_thread(prune, settings, "postgres-")
    finally:
        if plain.exists():
            plain.unlink()
    return encrypted


def checksum_matches(path: Path) -> bool:
    """Validate the stored SHA-256 sidecar."""
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.exists():
        return False
    expected = sidecar.read_text(encoding="utf-8").split()[0]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest == expected
