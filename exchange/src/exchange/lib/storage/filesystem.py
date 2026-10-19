"""Local development blob store used when MinIO is unavailable.

This backend is never allowed in production; it exists so the API can be
exercised on machines without an S3-compatible service.
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from exchange.lib.storage.s3 import StorageUnavailable
from exchange.models.ports.storage import StoredObject


class FilesystemBlobStore:
    """Store encrypted payloads under a local directory."""

    def __init__(self, directory: str) -> None:
        self._root = Path(directory).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self._root / key).resolve()
        if not candidate.is_relative_to(self._root):
            raise StorageUnavailable("invalid storage key")
        return candidate

    async def put(self, key: str, payload: bytes) -> StoredObject:
        """Write bytes atomically and return their checksum."""
        path = self._path(key)
        await asyncio.to_thread(self._write, path, payload)
        return StoredObject(
            key=key, size=len(payload), checksum_sha256=hashlib.sha256(payload).hexdigest()
        )

    async def get(self, key: str) -> bytes:
        """Read bytes by key."""
        path = self._path(key)
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError as exc:
            raise StorageUnavailable("object not found") from exc

    async def delete(self, key: str) -> None:
        """Delete idempotently."""
        path = self._path(key)
        await asyncio.to_thread(path.unlink, True)

    async def presign_put(self, key: str, content_type: str, ttl: int) -> str:
        """Direct uploads require a real object store."""
        raise StorageUnavailable("direct uploads require the s3 backend")

    async def presign_get(self, key: str, ttl: int) -> str:
        """Downloads require a real object store."""
        raise StorageUnavailable("downloads require the s3 backend")

    @staticmethod
    def _write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)
