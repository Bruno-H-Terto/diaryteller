"""Per-context key derivation and encrypted JSON payloads."""

from __future__ import annotations

import base64
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from diary_security import decrypt_json, encrypt_json

INFO = b"diary-exchange-context-v1"


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def derive_key(encoded_master: str, context_id: UUID) -> str:
    """Derive a stable 32-byte key per context without storing it."""
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=context_id.bytes,
        info=INFO,
    ).derive(_decode(encoded_master))
    return base64.urlsafe_b64encode(derived).decode()


def seal_payload(encoded_master: str, context_id: UUID, payload: dict[str, Any]) -> bytes:
    """Encrypt a JSON payload into the bytes stored remotely."""
    return encrypt_json(payload, derive_key(encoded_master, context_id)).encode()


def open_payload(encoded_master: str, context_id: UUID, data: bytes) -> dict[str, Any]:
    """Decrypt a stored payload, rejecting tampering or key mismatches."""
    return decrypt_json(data.decode(), derive_key(encoded_master, context_id))
