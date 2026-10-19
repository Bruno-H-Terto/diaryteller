"""OIDC transaction, replay protection, provider trust and account linking."""

from __future__ import annotations

import httpx
import pytest
from helpers import (
    FakeOidcProvider,
    auth_headers,
    identity_for,
    register_and_login,
)

pytestmark = pytest.mark.integration

REDIRECT = "diary://oidc"
CHALLENGE = "a" * 43
VERIFIER = "b" * 43
DEVICE = "88888888-8888-4888-8888-888888888888"


@pytest.fixture()
def provider(monkeypatch):
    """Install a deterministic provider in the running container."""
    from identity.app import app

    container = app.state.container
    fake = FakeOidcProvider()
    monkeypatch.setitem(container.oidc_providers, "fake", fake)
    return fake


async def _start(client) -> dict:
    response = await client.post(
        "/v1/auth/oidc/transactions",
        json={
            "provider": "fake",
            "redirect_uri": REDIRECT,
            "device_id": DEVICE,
            "code_challenge": CHALLENGE,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _exchange(
    client: httpx.AsyncClient, transaction: dict, *, state: str | None = None
) -> httpx.Response:
    return await client.post(
        "/v1/auth/oidc/exchange",
        json={
            "transaction_id": transaction["transaction_id"],
            "code": "authorization-code",
            "state": transaction["state"] if state is None else state,
            "code_verifier": VERIFIER,
        },
    )


async def test_start_returns_url_and_state(client, provider) -> None:
    view = await _start(client)
    assert view["authorization_url"].startswith("https://issuer.test/authorize?")
    assert view["state"]
    assert provider.code_challenges == [CHALLENGE]


async def test_exchange_creates_verified_account(client, provider) -> None:
    provider.identity = identity_for()
    transaction = await _start(client)
    response = await _exchange(client, transaction)
    assert response.status_code == 200, response.text
    tokens = response.json()
    me = await client.get("/v1/me", headers=auth_headers(tokens))
    assert me.status_code == 200
    assert me.json()["email"] == "oidc@example.com"
    assert me.json()["email_verified"] is True
    assert provider.last_nonce_hash


async def test_transaction_cannot_be_replayed(client, provider) -> None:
    provider.identity = identity_for()
    transaction = await _start(client)
    first = await _exchange(client, transaction)
    assert first.status_code == 200, first.text
    replay = await _exchange(client, transaction)
    assert replay.status_code == 400
    assert replay.json()["code"] == "oidc_transaction_invalid"


async def test_state_mismatch_is_rejected(client, provider) -> None:
    provider.identity = identity_for()
    transaction = await _start(client)
    response = await _exchange(client, transaction, state="x" * 43)
    assert response.status_code == 400
    assert response.json()["code"] == "oidc_transaction_invalid"


async def test_unverified_email_cannot_create_account(client, provider) -> None:
    provider.identity = identity_for(verified=False)
    transaction = await _start(client)
    response = await _exchange(client, transaction)
    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"


async def test_unknown_provider_and_redirect_are_rejected(client, provider) -> None:
    unknown = await client.post(
        "/v1/auth/oidc/transactions",
        json={
            "provider": "missing",
            "redirect_uri": REDIRECT,
            "device_id": DEVICE,
            "code_challenge": CHALLENGE,
        },
    )
    assert unknown.status_code == 404
    redirect = await client.post(
        "/v1/auth/oidc/transactions",
        json={
            "provider": "fake",
            "redirect_uri": "https://evil.test/callback",
            "device_id": DEVICE,
            "code_challenge": CHALLENGE,
        },
    )
    assert redirect.status_code == 400


async def test_existing_email_requires_explicit_link_then_reuses_account(
    client, database, provider
) -> None:
    existing = await register_and_login(
        client, database, "oidc@example.com", "99999999-9999-4999-8999-999999999999"
    )
    me = await client.get("/v1/me", headers=auth_headers(existing))
    existing_id = me.json()["id"]
    provider.identity = identity_for(subject="subject-link")
    transaction = await _start(client)
    conflict = await _exchange(client, transaction)
    assert conflict.status_code == 409
    body = conflict.json()
    assert body["code"] == "account_link_required"
    link_token = body["details"]["link_token"]
    assert body["details"]["requires_existing_account_login"] is True
    linked = await client.post(
        "/v1/auth/oidc/link",
        headers=auth_headers(existing),
        json={"link_token": link_token},
    )
    assert linked.status_code == 204, linked.text
    provider.identity = identity_for(subject="subject-link")
    second = await _start(client)
    created = await _exchange(client, second)
    assert created.status_code == 200, created.text
    again = await client.get("/v1/me", headers=auth_headers(created.json()))
    assert again.json()["id"] == existing_id


async def test_link_requires_matching_authenticated_account(client, database, provider) -> None:
    await register_and_login(
        client, database, "target@example.com", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    )
    other = await register_and_login(
        client, database, "other@example.com", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    )
    provider.identity = identity_for(subject="subject-target", email="target@example.com")
    transaction = await _start(client)
    conflict = await _exchange(client, transaction)
    assert conflict.status_code == 409
    link_token = conflict.json()["details"]["link_token"]
    rejected = await client.post(
        "/v1/auth/oidc/link",
        headers=auth_headers(other),
        json={"link_token": link_token},
    )
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "account_link_required"
