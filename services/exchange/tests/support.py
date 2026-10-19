"""Test doubles shared by exchange integration tests."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field

from diary_contracts.authorization import AccountStatus
from diary_contracts.errors import DomainError, ErrorCode
from exchange.application.ports.identity import Principal
from exchange.application.ports.storage import StoredObject


class FakeAuthorizer:
    """Configurable identity decision without network calls."""

    def __init__(self) -> None:
        self.principal: Principal | None = None
        self.permissions: list[str] = []

    async def authorize(self, *, authorization: str, source: str, permission: str) -> Principal:
        """Return the configured principal or an auth error."""
        self.permissions.append(permission)
        if self.principal is None:
            raise DomainError(ErrorCode.AUTH_INVALID, 401, "Authentication required")
        return self.principal


@dataclass
class MemoryBlobStore:
    """In-memory blob store that records what was written."""

    objects: dict[str, bytes] = field(default_factory=dict)
    presigned: list[str] = field(default_factory=list)

    async def put(self, key: str, payload: bytes) -> StoredObject:
        """Store bytes and return their checksum."""
        self.objects[key] = payload
        return StoredObject(
            key=key, size=len(payload), checksum_sha256=hashlib.sha256(payload).hexdigest()
        )

    async def get(self, key: str) -> bytes:
        """Read stored bytes."""
        return self.objects[key]

    async def delete(self, key: str) -> None:
        """Remove stored bytes."""
        self.objects.pop(key, None)

    async def presign_put(self, key: str, content_type: str, ttl: int) -> str:
        """Return a deterministic URL."""
        self.presigned.append(key)
        return f"http://storage.test/{key}?put=1"

    async def presign_get(self, key: str, ttl: int) -> str:
        """Return a deterministic URL."""
        return f"http://storage.test/{key}?get=1"


def principal_for(user_id: str, plan_code: str = "free") -> Principal:
    """Build a principal for a test user id."""
    return Principal(
        user_id=uuid.UUID(user_id),
        session_id=uuid.uuid4(),
        account_status=AccountStatus.ACTIVE,
        plan_code=plan_code,
    )
