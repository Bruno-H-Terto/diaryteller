"""Authenticate and validate the encrypted operation context.

The server never stores or caches records between calls. Every tool invocation
must carry a token that binds audience, operation, permission and record set.
"""

from __future__ import annotations

from datetime import UTC, datetime

from diary_contracts.mcp import ContextTokenClaims
from diary_security import TokenError, context_digest, decrypt_json
from pydantic import ValidationError


class ContextRejected(Exception):
    """The context credential is missing, expired or not authorized."""


class ContextVerifier:
    """Decrypt and validate a context JWE."""

    def __init__(self, encoded_key: str, max_ttl_seconds: int) -> None:
        self._key = encoded_key
        self._max_ttl = max_ttl_seconds

    def verify(self, token: str, permission: str) -> ContextTokenClaims:
        """Return claims only when every binding check passes."""
        if not token:
            raise ContextRejected("missing context")
        try:
            payload = decrypt_json(token, self._key)
            claims = ContextTokenClaims.model_validate(payload)
        except (TokenError, ValidationError, ValueError) as exc:
            raise ContextRejected("invalid context") from exc
        moment = datetime.now(UTC)
        if claims.expires_at <= moment or claims.issued_at > moment:
            raise ContextRejected("expired context")
        if (claims.expires_at - claims.issued_at).total_seconds() > self._max_ttl:
            raise ContextRejected("context lifetime too long")
        if claims.permission != permission:
            raise ContextRejected("permission mismatch")
        records = [record.model_dump(mode="json") for record in claims.records]
        if context_digest(records) != claims.context_digest:
            raise ContextRejected("context digest mismatch")
        if len({record.id for record in claims.records}) != len(claims.records):
            raise ContextRejected("duplicate context ids")
        return claims
