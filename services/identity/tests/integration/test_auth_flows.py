"""Persisted authentication, rotation and revocation tests."""

from __future__ import annotations

import pytest
from helpers import register_and_login

pytestmark = pytest.mark.integration


async def test_register_login_and_entitlements(client, database) -> None:
    tokens = await register_and_login(
        client, database, "a@example.com", "11111111-1111-4111-8111-111111111111"
    )
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Session-Source": tokens["source"],
    }
    me = await client.get("/v1/me", headers=headers)
    assert me.status_code == 200 and me.json()["email_verified"] is True
    entitlements = await client.get("/v1/me/entitlements", headers=headers)
    assert entitlements.status_code == 200
    assert entitlements.json()["plan_code"] == "free"
    assert "memory:timeline" not in entitlements.json()["permissions"]


async def test_login_before_verification_is_blocked(client, database) -> None:
    await client.post(
        "/v1/auth/register",
        json={
            "email": "unverified@example.com",
            "password": "correct horse battery",
            "locale": "pt-BR",
            "timezone": "UTC",
        },
    )
    response = await client.post(
        "/v1/auth/login",
        json={
            "email": "unverified@example.com",
            "password": "correct horse battery",
            "device_id": "22222222-2222-4222-8222-222222222222",
            "platform": "android",
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"


async def test_refresh_rotation_and_reuse_revokes_session(client, database) -> None:
    tokens = await register_and_login(
        client, database, "refresh@example.com", "33333333-3333-4333-8333-333333333333"
    )
    device = "33333333-3333-4333-8333-333333333333"
    rotated = await client.post(
        "/v1/auth/refresh",
        headers={"X-Session-Source": tokens["source"]},
        json={"refresh_token": tokens["refresh_token"], "device_id": device},
    )
    assert rotated.status_code == 200
    new_tokens = rotated.json()
    reuse = await client.post(
        "/v1/auth/refresh",
        headers={"X-Session-Source": tokens["source"]},
        json={"refresh_token": tokens["refresh_token"], "device_id": device},
    )
    assert reuse.status_code == 401 and reuse.json()["code"] == "session_revoked"
    headers = {
        "Authorization": f"Bearer {new_tokens['access_token']}",
        "X-Session-Source": new_tokens["source"],
    }
    assert (await client.get("/v1/me", headers=headers)).status_code == 401


async def test_source_from_another_session_is_rejected(client, database) -> None:
    first = await register_and_login(
        client, database, "multi@example.com", "44444444-4444-4444-8444-444444444444"
    )
    second = await register_and_login(
        client, database, "multi@example.com", "55555555-5555-4555-8555-555555555555"
    )
    response = await client.get(
        "/v1/me",
        headers={
            "Authorization": f"Bearer {first['access_token']}",
            "X-Session-Source": second["source"],
        },
    )
    assert response.status_code == 401


async def test_account_deletion_revokes_immediately(client, database) -> None:
    tokens = await register_and_login(
        client, database, "delete@example.com", "66666666-6666-4666-8666-666666666666"
    )
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Session-Source": tokens["source"],
    }
    deleted = await client.delete("/v1/me", headers=headers)
    assert deleted.status_code == 202
    assert (await client.get("/v1/me", headers=headers)).status_code == 401
