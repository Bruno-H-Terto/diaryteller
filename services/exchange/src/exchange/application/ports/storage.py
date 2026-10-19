"""Object storage port used for encrypted payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredObject:
    """Object metadata returned after a write."""

    key: str
    size: int
    checksum_sha256: str


class BlobStore(Protocol):
    """Encrypted blob persistence in an S3-compatible store."""

    async def put(self, key: str, payload: bytes) -> StoredObject:
        """Write a payload and return its size and checksum."""
        ...

    async def get(self, key: str) -> bytes:
        """Read a payload by key."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a payload; missing keys are ignored."""
        ...

    async def presign_put(self, key: str, content_type: str, ttl: int) -> str:
        """Return a URL the client can PUT to."""
        ...

    async def presign_get(self, key: str, ttl: int) -> str:
        """Return a URL the client can GET from."""
        ...
