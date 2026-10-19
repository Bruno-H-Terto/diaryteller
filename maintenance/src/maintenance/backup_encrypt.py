"""Streaming AES-256-GCM encryption for administrative backups.

The output is `magic || nonce || ciphertext || tag`. No diary content exists in
these backups; encryption protects account, session and billing metadata.
"""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MAGIC = b"DIARYBKP1"
CHUNK = 1024 * 1024
NONCE_SIZE = 12
TAG_SIZE = 16


def _key(encoded: str) -> bytes:
    value = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    if len(value) != 32:
        raise ValueError("backup key must be 32 bytes")
    return value


def encrypt_file(source: Path, destination: Path, encoded_key: str) -> str:
    """Encrypt in chunks and return the SHA-256 of the encrypted file."""
    nonce = os.urandom(NONCE_SIZE)
    encryptor = Cipher(algorithms.AES(_key(encoded_key)), modes.GCM(nonce)).encryptor()
    digest = hashlib.sha256()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("wb") as dst:
        dst.write(MAGIC + nonce)
        digest.update(MAGIC + nonce)
        while chunk := src.read(CHUNK):
            encrypted = encryptor.update(chunk)
            dst.write(encrypted)
            digest.update(encrypted)
        dst.write(encryptor.finalize())
        dst.write(encryptor.tag)
        digest.update(encryptor.tag)
    destination.chmod(0o600)
    return digest.hexdigest()


def decrypt_file(source: Path, destination: Path, encoded_key: str) -> None:
    """Decrypt to a temporary target, verifying the authentication tag."""
    raw_size = source.stat().st_size
    if raw_size < len(MAGIC) + NONCE_SIZE + TAG_SIZE:
        raise ValueError("backup is truncated")
    with source.open("rb") as src:
        if src.read(len(MAGIC)) != MAGIC:
            raise ValueError("backup magic mismatch")
        nonce = src.read(NONCE_SIZE)
        tag = b""
        src.seek(raw_size - TAG_SIZE)
        tag = src.read(TAG_SIZE)
        src.seek(len(MAGIC) + NONCE_SIZE)
        remaining = raw_size - len(MAGIC) - NONCE_SIZE - TAG_SIZE
        decryptor = Cipher(algorithms.AES(_key(encoded_key)), modes.GCM(nonce, tag)).decryptor()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as dst:
            while remaining > 0:
                chunk = src.read(min(CHUNK, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                dst.write(decryptor.update(chunk))
            dst.write(decryptor.finalize())
    destination.chmod(0o600)
