"""Single-use email token generation with encrypted delivery material.

The database stores only the digest. The outbox carries an encrypted secret so
the notifications worker can build the link without a plaintext token at rest.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from diary_security import encrypt_json, sha256_digest


@dataclass(frozen=True, slots=True)
class EmailToken:
    """Token material split between the digest and delivery ciphertext."""

    token: str
    digest: str
    ciphertext: str


def create_email_token(purpose: str, encoded_key: str) -> EmailToken:
    """Create a random token for `verify-email` or `password-reset`."""
    token = secrets.token_urlsafe(32)
    return EmailToken(
        token=token,
        digest=sha256_digest(token),
        ciphertext=encrypt_json({"purpose": purpose, "token": token}, encoded_key),
    )
