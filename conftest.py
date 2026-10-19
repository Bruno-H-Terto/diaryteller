"""Test configuration: isolate databases, keys and deterministic providers."""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def _secret() -> str:
    return base64.urlsafe_b64encode(b"t" * 32).decode()


_KEY_DIR = Path(tempfile.mkdtemp(prefix="diary-test-keys-"))


def _write_keys() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    (_KEY_DIR / "test-1.private.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    (_KEY_DIR / "test-1.public.pem").write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


_write_keys()
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://diary:diary@localhost:5432/diary_test"
)
os.environ["MONGO_URL"] = os.environ.get("TEST_MONGO_URL", "mongodb://localhost:57017")
os.environ["JWT_KEYS_DIR"] = str(_KEY_DIR)
os.environ["JWT_ACTIVE_KID"] = "test-1"
os.environ["SOURCE_ENCRYPTION_KEY"] = _secret()
os.environ["MCP_CONTEXT_KEY"] = _secret()
os.environ["EMAIL_TOKEN_KEY"] = _secret()
os.environ["PUSH_TOKEN_KEY"] = _secret()
os.environ["BILLING_TOKEN_KEY"] = _secret()
os.environ["IDEMPOTENCY_HMAC_KEY"] = _secret()
os.environ["BACKUP_ENCRYPTION_KEY"] = _secret()
os.environ["BILLING_PROVIDER"] = "fake"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["PUSH_PROVIDER"] = "dev"
os.environ["CONVERSATION_INTERNAL_TOKEN"] = "test-conversation"
os.environ["IDENTITY_INTERNAL_SECRETS"] = (
    '{"conversation":"test-conversation","exchange":"test-exchange"}'
)
os.environ["OIDC_ENABLED"] = "true"
os.environ["OIDC_ALLOWED_REDIRECT_URIS"] = '["diary://oidc"]'
os.environ["OIDC_PROVIDERS"] = (
    '{"fake":{"discovery_url":"https://issuer.test/.well-known/openid-configuration",'
    '"client_id":"app","client_secret":"secret"}}'
)
os.environ["MCP_SERVICE_TOKEN"] = "test-mcp"
os.environ["IDENTITY_INTERNAL_URL"] = "http://identity"
os.environ["MCP_URL"] = "http://memory/mcp"
os.environ["EXCHANGE_DATABASE_URL"] = os.environ.get(
    "TEST_EXCHANGE_DATABASE_URL", "postgresql+asyncpg://diary:diary@localhost:5432/exchange_test"
)
os.environ["EXCHANGE_CONTEXT_ENCRYPTION_KEY"] = _secret()
os.environ["EXCHANGE_IDENTITY_INTERNAL_URL"] = "http://identity"
os.environ["EXCHANGE_IDENTITY_INTERNAL_TOKEN"] = "test-exchange"
os.environ["EXCHANGE_INTERNAL_SECRETS"] = '{"conversation":"test-conversation"}'


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio for all async tests."""
    return "asyncio"
