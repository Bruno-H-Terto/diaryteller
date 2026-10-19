"""RS256 access tokens with explicit kid selection and validation.

Only asymmetric RS256 is accepted. Verification restricts algorithms, issuer,
audience and required claims with a small clock tolerance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import jwt

REQUIRED_CLAIMS = ("iss", "aud", "sub", "sid", "iat", "exp", "jti")


class TokenInvalid(Exception):
    """Raised when an access token is missing, expired or forged."""


@dataclass(frozen=True, slots=True)
class AccessClaims:
    """Validated access token claims."""

    user_id: UUID
    session_id: UUID
    jti: str
    issued_at: datetime
    expires_at: datetime


class AccessTokenIssuer:
    """Sign and verify access tokens using PEM keys named by `kid`."""

    def __init__(
        self,
        keys_dir: Path,
        active_kid: str,
        issuer: str,
        audience: str,
        ttl_seconds: int,
        leeway_seconds: int,
    ) -> None:
        self._keys_dir = keys_dir
        self._active_kid = active_kid
        self._issuer = issuer
        self._audience = audience
        self._ttl = ttl_seconds
        self._leeway = leeway_seconds
        self._private = self._read(active_kid, "private")
        self._public: dict[str, str] = {}
        self._load_public_keys()

    def _read(self, kid: str, kind: str) -> str:
        path = self._keys_dir / f"{kid}.{kind}.pem"
        if not path.is_file():
            raise RuntimeError(f"missing {kind} key for kid {kid}")
        return path.read_text(encoding="utf-8")

    def _load_public_keys(self) -> None:
        for path in self._keys_dir.glob("*.public.pem"):
            self._public[path.name.removesuffix(".public.pem")] = path.read_text(encoding="utf-8")
        if self._active_kid not in self._public:
            self._public[self._active_kid] = self._read(self._active_kid, "public")

    def issue(self, user_id: UUID, session_id: UUID, now: datetime | None = None) -> str:
        """Issue a short access token bound to one persisted session."""
        moment = now or datetime.now(UTC)
        payload = {
            "iss": self._issuer,
            "aud": self._audience,
            "sub": str(user_id),
            "sid": str(session_id),
            "iat": int(moment.timestamp()),
            "exp": int((moment + timedelta(seconds=self._ttl)).timestamp()),
            "jti": str(uuid4()),
        }
        return jwt.encode(
            payload,
            self._private,
            algorithm="RS256",
            headers={"kid": self._active_kid, "typ": "JWT"},
        )

    def verify(self, token: str) -> AccessClaims:
        """Validate a token and return claims, raising `TokenInvalid`."""
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not isinstance(kid, str) or kid not in self._public:
                raise TokenInvalid("unknown key")
            payload = jwt.decode(
                token,
                self._public[kid],
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": list(REQUIRED_CLAIMS)},
            )
            return AccessClaims(
                user_id=UUID(payload["sub"]),
                session_id=UUID(payload["sid"]),
                jti=str(payload["jti"]),
                issued_at=datetime.fromtimestamp(payload["iat"], UTC),
                expires_at=datetime.fromtimestamp(payload["exp"], UTC),
            )
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
            raise TokenInvalid("invalid access token") from exc
