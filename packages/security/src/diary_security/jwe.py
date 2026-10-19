"""Small, explicit JWE helper for short-lived opaque tokens.

Only direct AES-256-GCM compact JWE is accepted. Callers validate their own
claims (audience, purpose, expiry) after decryption.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from joserfc import jwe
from joserfc.errors import JoseError
from joserfc.jwk import OctKey

ALGORITHMS = ("dir", "A256GCM")


class TokenError(Exception):
    """Raised for malformed, tampered or undecryptable tokens."""


def _key(encoded: str) -> OctKey:
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except Exception as exc:
        raise TokenError("invalid key encoding") from exc
    if len(raw) != 32:
        raise TokenError("invalid key length")
    return OctKey.import_key(
        {"kty": "oct", "k": base64.urlsafe_b64encode(raw).decode().rstrip("=")}
    )


def encrypt_json(payload: dict[str, Any], encoded_key: str) -> str:
    """Encrypt a JSON object with AES-256-GCM and return a compact JWE."""
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return jwe.encrypt_compact(
        {"alg": "dir", "enc": "A256GCM", "cty": "json"},
        plaintext,
        _key(encoded_key),
        algorithms=list(ALGORITHMS),
    )


def decrypt_json(token: str, encoded_key: str) -> dict[str, Any]:
    """Decrypt and parse a compact JWE, raising `TokenError` on any failure."""
    try:
        result = jwe.decrypt_compact(token, _key(encoded_key), algorithms=list(ALGORITHMS))
        plaintext = result.plaintext
        if plaintext is None:
            raise TokenError("empty token payload")
        value = json.loads(plaintext)
    except (JoseError, ValueError, TypeError) as exc:
        raise TokenError("invalid token") from exc
    if not isinstance(value, dict):
        raise TokenError("invalid token payload")
    return value
