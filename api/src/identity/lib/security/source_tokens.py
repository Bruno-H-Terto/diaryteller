"""Encrypted session-source token bound to a device and session version."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from diary_security import TokenError, decrypt_json, encrypt_json

PURPOSE = "session-source"


class SourceInvalid(Exception):
    """Raised when the encrypted source is invalid or belongs elsewhere."""


@dataclass(frozen=True, slots=True)
class SourceClaims:
    """Validated source claims."""

    session_id: UUID
    device_id: UUID
    source_version: int
    issued_at: datetime
    expires_at: datetime


class SourceTokenCodec:
    """Issue and validate `X-Session-Source` using a dedicated AES key."""

    def __init__(
        self,
        encoded_key: str,
        *,
        issuer: str,
        audience: str,
        ttl_seconds: int,
        leeway_seconds: int = 10,
    ) -> None:
        self._key = encoded_key
        self._issuer = issuer
        self._audience = audience
        self._ttl = ttl_seconds
        self._leeway = leeway_seconds

    def issue(
        self,
        session_id: UUID,
        device_id: UUID,
        source_version: int,
        now: datetime | None = None,
    ) -> str:
        """Issue an encrypted source token for the current session version."""
        moment = now or datetime.now(UTC)
        return encrypt_json(
            {
                "iss": self._issuer,
                "aud": self._audience,
                "purpose": PURPOSE,
                "sid": str(session_id),
                "device_id": str(device_id),
                "source_version": source_version,
                "iat": int(moment.timestamp()),
                "exp": int((moment + timedelta(seconds=self._ttl)).timestamp()),
            },
            self._key,
        )

    def verify(self, token: str, now: datetime | None = None) -> SourceClaims:
        """Validate audience, purpose, issuer and expiry."""
        moment = now or datetime.now(UTC)
        try:
            payload = decrypt_json(token, self._key)
            if payload.get("aud") != self._audience:
                raise SourceInvalid("audience mismatch")
            if payload.get("iss") != self._issuer or payload.get("purpose") != PURPOSE:
                raise SourceInvalid("purpose mismatch")
            expires = datetime.fromtimestamp(int(payload["exp"]), UTC)
            if expires + timedelta(seconds=self._leeway) < moment:
                raise SourceInvalid("expired source")
            return SourceClaims(
                session_id=UUID(payload["sid"]),
                device_id=UUID(payload["device_id"]),
                source_version=int(payload["source_version"]),
                issued_at=datetime.fromtimestamp(int(payload["iat"]), UTC),
                expires_at=expires,
            )
        except (TokenError, KeyError, TypeError, ValueError) as exc:
            raise SourceInvalid("invalid source token") from exc
