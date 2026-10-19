"""Create the short-lived encrypted context credential injected into MCP calls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from diary_contracts.authorization import Permission
from diary_contracts.context import ContextBundle
from diary_contracts.mcp import ContextTokenClaims
from diary_security import context_digest, encrypt_json


class ContextBinder:
    """Bind one operation and one selected record set into a JWE."""

    def __init__(self, encoded_key: str, ttl_seconds: int) -> None:
        self._key = encoded_key
        self._ttl = ttl_seconds

    def create(
        self,
        *,
        context: ContextBundle,
        operation_id: UUID,
        user_id: UUID,
        session_id: UUID,
        permission: Permission,
        now: datetime | None = None,
    ) -> str:
        """Return an encrypted token the model never sees or controls."""
        moment = now or datetime.now(UTC)
        records = [record.model_dump(mode="json") for record in context.records]
        claims = ContextTokenClaims(
            operation_id=operation_id,
            user_id=user_id,
            session_id=session_id,
            permission=permission.value,
            records=context.records,
            issued_at=moment,
            expires_at=moment + timedelta(seconds=self._ttl),
            context_digest=context_digest(records),
        )
        return encrypt_json(claims.model_dump(mode="json"), self._key)
