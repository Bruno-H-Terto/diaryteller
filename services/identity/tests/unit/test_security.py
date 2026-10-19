"""Password, access-token and source-token tests."""

from __future__ import annotations

import base64
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from identity.adapters.security.access_tokens import AccessTokenIssuer, TokenInvalid
from identity.adapters.security.passwords import PasswordHasher
from identity.adapters.security.source_tokens import SourceInvalid, SourceTokenCodec


def issuer() -> AccessTokenIssuer:
    directory = Path(tempfile.mkdtemp())
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    (directory / "k1.private.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    (directory / "k1.public.pem").write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return AccessTokenIssuer(directory, "k1", "iss", "aud", 600, 5)


async def test_password_hash_and_verify() -> None:
    hasher = PasswordHasher(time_cost=1, memory_kib=8192, parallelism=1, concurrency=2)
    encoded = await hasher.hash("correct horse battery")
    assert (await hasher.verify("correct horse battery", encoded)).valid
    assert not (await hasher.verify("wrong password", encoded)).valid


def test_access_token_roundtrip_and_tamper() -> None:
    service = issuer()
    user_id, session_id = uuid4(), uuid4()
    token = service.issue(user_id, session_id)
    claims = service.verify(token)
    assert claims.user_id == user_id and claims.session_id == session_id
    with pytest.raises(TokenInvalid):
        service.verify(token[:-2] + "aa")


def test_source_token_requires_same_key_and_audience() -> None:
    key = base64.urlsafe_b64encode(b"s" * 32).decode()
    codec = SourceTokenCodec(key, issuer="iss", audience="aud", ttl_seconds=60)
    session_id, device_id = uuid4(), uuid4()
    claims = codec.verify(codec.issue(session_id, device_id, 2))
    assert claims.session_id == session_id and claims.source_version == 2
    with pytest.raises(SourceInvalid):
        codec.verify(
            codec.issue(session_id, device_id, 2), now=datetime.now(UTC) + timedelta(hours=1)
        )
