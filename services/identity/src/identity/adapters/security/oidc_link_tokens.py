"""Short-lived encrypted token authorizing one OIDC account link.

The token never proves a password by itself: it is only honored for an already
authenticated session whose email matches the provider's verified email.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from diary_security import TokenError, decrypt_json, encrypt_json

PURPOSE = "oidc-link"


class LinkTokenInvalid(Exception):
    """Raised when a link token is malformed, expired or from elsewhere."""


@dataclass(frozen=True, slots=True)
class LinkClaims:
    """Validated provider identity awaiting an explicit account link."""

    provider: str
    issuer: str
    subject: str
    email: str
    expires_at: datetime


class OidcLinkTokenCodec:
    """Issue and verify link tokens with a dedicated AES key."""

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
        *,
        provider: str,
        issuer: str,
        subject: str,
        email: str,
        now: datetime | None = None,
    ) -> str:
        """Issue a token bound to one external identity and verified email."""
        moment = now or datetime.now(UTC)
        return encrypt_json(
            {
                "iss": self._issuer,
                "aud": self._audience,
                "purpose": PURPOSE,
                "provider": provider,
                "ext_iss": issuer,
                "sub": subject,
                "email": email,
                "iat": int(moment.timestamp()),
                "exp": int((moment + timedelta(seconds=self._ttl)).timestamp()),
            },
            self._key,
        )

    def verify(self, token: str, now: datetime | None = None) -> LinkClaims:
        """Validate audience, purpose, issuer and expiry."""
        moment = now or datetime.now(UTC)
        try:
            payload = decrypt_json(token, self._key)
            if payload.get("aud") != self._audience:
                raise LinkTokenInvalid("audience mismatch")
            if payload.get("iss") != self._issuer or payload.get("purpose") != PURPOSE:
                raise LinkTokenInvalid("purpose mismatch")
            expires = datetime.fromtimestamp(int(payload["exp"]), UTC)
            if expires + timedelta(seconds=self._leeway) < moment:
                raise LinkTokenInvalid("expired link token")
            email = payload["email"]
            if not isinstance(email, str) or not email:
                raise LinkTokenInvalid("missing email")
            return LinkClaims(
                provider=str(payload["provider"]),
                issuer=str(payload["ext_iss"]),
                subject=str(payload["sub"]),
                email=email.lower(),
                expires_at=expires,
            )
        except (TokenError, KeyError, TypeError, ValueError) as exc:
            raise LinkTokenInvalid("invalid link token") from exc
