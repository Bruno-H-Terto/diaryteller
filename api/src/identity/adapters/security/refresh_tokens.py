"""Opaque high-entropy refresh tokens stored only as digests."""

from __future__ import annotations

import secrets

from diary_security import sha256_digest

TOKEN_BYTES = 48


def new_refresh_token() -> tuple[str, str]:
    """Return a random token and its digest; only the digest is stored."""
    token = secrets.token_urlsafe(TOKEN_BYTES)
    return token, sha256_digest(token)


def refresh_digest(token: str) -> str:
    """Digest a presented token for indexed lookup."""
    return sha256_digest(token)
