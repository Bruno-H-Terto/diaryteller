"""Helpers shared by identity integration tests."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from identity.adapters.oidc import OidcIdentity, OidcInvalidToken
from sqlalchemy.ext.asyncio import create_async_engine


async def verify_email(email: str, database: str) -> None:
    """Mark an account verified without inspecting the email token."""
    engine = create_async_engine(database)
    try:
        async with engine.begin() as connection:
            from sqlalchemy import text

            await connection.execute(
                text("UPDATE users SET email_verified_at = now() WHERE email = :email"),
                {"email": email},
            )
    finally:
        await engine.dispose()


async def register_and_login(
    client: httpx.AsyncClient, database: str, email: str, device: str
) -> dict:
    register = await client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": "correct horse battery",
            "locale": "pt-BR",
            "timezone": "UTC",
        },
    )
    assert register.status_code == 201, register.text
    await verify_email(email, database)
    login = await client.post(
        "/v1/auth/login",
        json={
            "email": email,
            "password": "correct horse battery",
            "device_id": device,
            "platform": "android",
        },
    )
    assert login.status_code == 200, login.text
    return login.json()


@dataclass
class FakeOidcProvider:
    """Stand-in for a configured provider; no network is involved."""

    name: str = "fake"
    identity: OidcIdentity | None = None
    last_nonce_hash: str = ""
    code_challenges: list[str] = field(default_factory=list)

    async def authorization_url(
        self, *, redirect_uri: str, state: str, nonce: str, code_challenge: str
    ) -> str:
        """Return a deterministic external URL."""
        self.code_challenges.append(code_challenge)
        return f"https://issuer.test/authorize?state={state}&redirect_uri={redirect_uri}"

    async def exchange(
        self, *, code: str, redirect_uri: str, code_verifier: str, nonce_hash: str
    ) -> OidcIdentity:
        """Return the configured identity or fail like the real adapter."""
        self.last_nonce_hash = nonce_hash
        if self.identity is None:
            raise OidcInvalidToken("no identity configured")
        return self.identity


def identity_for(
    subject: str = "subject-1",
    email: str = "oidc@example.com",
    *,
    verified: bool = True,
) -> OidcIdentity:
    """Build a provider identity for a test."""
    return OidcIdentity(
        issuer="https://issuer.test",
        subject=subject,
        provider="fake",
        email=email,
        email_verified=verified,
        name="OIDC User",
    )


def auth_headers(tokens: dict) -> dict[str, str]:
    """Authenticated request headers for a login bundle."""
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Session-Source": tokens["source"],
    }


def internal_headers(service: str = "exchange", token: str = "test-exchange") -> dict[str, str]:
    """Trusted-service headers for the internal quota API."""
    return {"X-Internal-Service": service, "X-Internal-Token": token}


async def owner_and_tokens(
    client: httpx.AsyncClient, database: str, email: str, device: str
) -> tuple[dict, str]:
    """Register, verify, log in and return the credential bundle and user id."""
    tokens = await register_and_login(client, database, email, device)
    me = await client.get("/v1/me", headers=auth_headers(tokens))
    assert me.status_code == 200, me.text
    return tokens, me.json()["id"]
