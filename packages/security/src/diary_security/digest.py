"""Keyed digests and canonical JSON used for idempotency and context binding."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Serialize deterministically for hashing (no floats in payloads)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_digest(value: str) -> str:
    """Return a hex SHA-256 digest of a high-entropy token."""
    return hashlib.sha256(value.encode()).hexdigest()


def hmac_digest(key: str, value: Any) -> str:
    """Return a hex HMAC-SHA256 over canonical JSON.

    The key must be a server-side secret with a dedicated purpose; the digest is
    never compared to plain text stored by callers.
    """
    return hmac.new(key.encode(), canonical_json(value), hashlib.sha256).hexdigest()


def context_digest(records: list[dict[str, Any]]) -> str:
    """Bind an authorized record set to one operation."""
    return hashlib.sha256(canonical_json(records)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    """Hex digest of binary payload bytes (never stored)."""
    return hashlib.sha256(value).hexdigest()
