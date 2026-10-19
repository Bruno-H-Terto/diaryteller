"""JWE and digest tests."""

from __future__ import annotations

import base64

import pytest
from diary_security import (
    TokenError,
    context_digest,
    decrypt_json,
    encrypt_json,
    hmac_digest,
)


def key() -> str:
    return base64.urlsafe_b64encode(b"k" * 32).decode()


def test_jwe_roundtrip() -> None:
    token = encrypt_json({"sub": "x", "exp": 1}, key())
    assert decrypt_json(token, key()) == {"sub": "x", "exp": 1}


def test_tampered_token_rejected() -> None:
    token = encrypt_json({"sub": "x"}, key())
    with pytest.raises(TokenError):
        decrypt_json(token[:-2] + "aa", key())


def test_wrong_key_rejected() -> None:
    token = encrypt_json({"sub": "x"}, key())
    other = base64.urlsafe_b64encode(b"z" * 32).decode()
    with pytest.raises(TokenError):
        decrypt_json(token, other)


def test_context_digest_is_stable() -> None:
    records = [{"id": "a", "text": "b"}]
    assert context_digest(records) == context_digest([{"text": "b", "id": "a"}])


def test_hmac_changes_with_key() -> None:
    assert hmac_digest("a" * 16, {"x": 1}) != hmac_digest("b" * 16, {"x": 1})
