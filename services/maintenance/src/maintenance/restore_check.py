"""Verify that encrypted administrative backups can be read/restored."""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

from maintenance.backup_encrypt import decrypt_file
from maintenance.backup_postgres import checksum_matches
from maintenance.settings import MaintenanceSettings


def _latest(directory: Path, prefix: str) -> Path:
    files = sorted(directory.glob(f"{prefix}*.enc"))
    if not files:
        raise FileNotFoundError(f"no {prefix} backup found")
    return files[-1]


def _verify_postgres(settings: MaintenanceSettings, path: Path) -> None:
    result = subprocess.run(
        [settings.pg_restore_binary, "--list", str(path)],
        capture_output=True,
        timeout=settings.backup_timeout_seconds,
        check=False,
        env=os.environ,
    )
    if result.returncode != 0:
        raise RuntimeError("pg_restore could not read the archive")


def _verify_mongo(settings: MaintenanceSettings, path: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as config:
        config.write(f"uri: {settings.mongo_url}\n")
        config_path = Path(config.name)
    config_path.chmod(0o600)
    try:
        result = subprocess.run(
            [
                settings.mongorestore_binary,
                "--config",
                str(config_path),
                f"--archive={path}",
                "--gzip",
                "--dryRun",
            ],
            capture_output=True,
            timeout=settings.backup_timeout_seconds,
            check=False,
            env=os.environ,
        )
    finally:
        config_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError("mongorestore dry run failed")


def _restore_postgres(settings: MaintenanceSettings, path: Path) -> None:
    if not settings.restore_target_database_url:
        return
    result = subprocess.run(
        [
            settings.pg_restore_binary,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-acl",
            "--dbname",
            settings.restore_target_database_url.replace("+asyncpg", ""),
            str(path),
        ],
        capture_output=True,
        timeout=settings.backup_timeout_seconds,
        check=False,
        env=os.environ,
    )
    if result.returncode != 0:
        raise RuntimeError("pg_restore failed")


async def verify_latest(settings: MaintenanceSettings) -> dict[str, str]:
    """Decrypt and validate the newest PostgreSQL and Mongo archives."""
    directory = Path(settings.backup_dir)
    results: dict[str, str] = {}
    for kind, prefix in (("postgres", "postgres-"), ("mongo", "mongo-")):
        try:
            encrypted = _latest(directory, prefix)
        except FileNotFoundError:
            results[kind] = "missing"
            continue
        if not checksum_matches(encrypted):
            results[kind] = "checksum_mismatch"
            continue
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "restore.bin"
            try:
                await asyncio.to_thread(
                    decrypt_file, encrypted, target, settings.backup_encryption_key
                )
            except Exception:
                results[kind] = "decrypt_failed"
                continue
            if kind == "postgres":
                await asyncio.to_thread(_verify_postgres, settings, target)
                await asyncio.to_thread(_restore_postgres, settings, target)
                results[kind] = "verified"
            else:
                await asyncio.to_thread(_verify_mongo, settings, target)
                results[kind] = "verified"
    return results
