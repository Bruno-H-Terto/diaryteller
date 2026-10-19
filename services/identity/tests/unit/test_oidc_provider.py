"""ID token validation: signature, audience, issuer, expiry and nonce."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from diary_security import sha256_digest
from identity.adapters.oidc import OidcInvalidToken, OidcProviderClient
from identity.settings import OidcProviderSettings
from jwt.algorithms import RSAAlgorithm

ISSUER = "https://issuer.test"
CLIENT_ID = "mobile-app"
NONCE = "nonce-value"
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"


def _signing_key() -> tuple[Any, dict[str, Any]]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk: dict[str, Any] = json.loads(RSAAlgorithm.to_jwk(private.public_key()))
    jwk.update({"kid": "key-1", "alg": "RS256", "use": "sig"})
    return private, jwk


def _client(private: Any, jwk: dict[str, Any], claims: dict[str, Any]) -> OidcProviderClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "issuer": ISSUER,
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": f"{ISSUER}/jwks",
                },
            )
        if request.url.path == "/jwks":
            return httpx.Response(200, json={"keys": [jwk]})
        if request.url.path == "/token":
            token = jwt.encode(claims, private, algorithm="RS256", headers={"kid": "key-1"})
            return httpx.Response(200, json={"id_token": token, "access_token": "ignored"})
        return httpx.Response(404)

    config = OidcProviderSettings(
        discovery_url=DISCOVERY_URL, client_id=CLIENT_ID, client_secret="secret"
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OidcProviderClient("fake", config, http)


def _claims(**overrides: Any) -> dict[str, Any]:
    now = int(time.time())
    base = {
        "iss": ISSUER,
        "sub": "subject-1",
        "aud": CLIENT_ID,
        "iat": now,
        "exp": now + 300,
        "nonce": NONCE,
        "email": "User@Example.com",
        "email_verified": True,
    }
    base.update(overrides)
    return base


async def _exchange(provider: OidcProviderClient, nonce_hash: str) -> Any:
    return await provider.exchange(
        code="code",
        redirect_uri="diary://oidc",
        code_verifier="c" * 43,
        nonce_hash=nonce_hash,
    )


async def test_valid_token_returns_normalized_identity() -> None:
    private, jwk = _signing_key()
    provider = _client(private, jwk, _claims())
    identity = await _exchange(provider, sha256_digest(NONCE))
    assert identity.subject == "subject-1"
    assert identity.email == "user@example.com"
    assert identity.email_verified is True
    assert identity.issuer == ISSUER


@pytest.mark.parametrize(
    "claims",
    [
        _claims(nonce="other"),
        _claims(aud="other-app"),
        _claims(iss="https://attacker.test"),
        _claims(exp=int(time.time()) - 3600),
        _claims(azp="other-app"),
    ],
)
async def test_invalid_claims_are_rejected(claims: dict[str, Any]) -> None:
    private, jwk = _signing_key()
    provider = _client(private, jwk, claims)
    with pytest.raises(OidcInvalidToken):
        await _exchange(provider, sha256_digest(NONCE))


async def test_signature_from_another_key_is_rejected() -> None:
    _, jwk = _signing_key()
    other_private, _ = _signing_key()
    token = jwt.encode(_claims(), other_private, algorithm="RS256", headers={"kid": "key-1"})

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "issuer": ISSUER,
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": f"{ISSUER}/jwks",
                },
            )
        if request.url.path == "/jwks":
            return httpx.Response(200, json={"keys": [jwk]})
        return httpx.Response(200, json={"id_token": token})

    config = OidcProviderSettings(discovery_url=DISCOVERY_URL, client_id=CLIENT_ID)
    provider = OidcProviderClient(
        "fake", config, httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(OidcInvalidToken):
        await _exchange(provider, sha256_digest(NONCE))
