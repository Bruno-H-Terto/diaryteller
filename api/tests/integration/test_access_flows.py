"""Quota, operation ownership, billing and plan-boundary tests."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime

import pytest
from helpers import register_and_login

pytestmark = pytest.mark.integration

INTERNAL = {
    "X-Internal-Service": "conversation",
    "X-Internal-Token": "test-conversation",
}


def app_headers(tokens: dict) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Session-Source": tokens["source"],
        **INTERNAL,
    }


def reserve_body(key: str, digest: str = "a" * 32) -> dict:
    return {
        "operation_type": "ai_response",
        "permission": "conversation:use",
        "idempotency_key": key,
        "payload_digest": digest,
        "metric": "ai_tokens",
        "estimated_amount": 16000,
    }


async def test_client_cannot_grant_plan(client, database) -> None:
    tokens = await register_and_login(
        client, database, "plan@example.com", "77777777-7777-4777-8777-777777777777"
    )
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Session-Source": tokens["source"],
    }
    response = await client.patch("/v1/me", headers=headers, json={"is_premium": True})
    assert response.status_code == 422


async def test_quota_is_atomic_under_concurrency(client, database) -> None:
    tokens = await register_and_login(
        client, database, "quota@example.com", "88888888-8888-4888-8888-888888888888"
    )
    headers = app_headers(tokens)
    first, second = await asyncio.gather(
        client.post(
            "/internal/operations/reserve", headers=headers, json=reserve_body("quota-key-1")
        ),
        client.post(
            "/internal/operations/reserve", headers=headers, json=reserve_body("quota-key-1x")
        ),
    )
    statuses = sorted([first.status_code, second.status_code])
    assert statuses == [200, 429]
    winner = first if first.status_code == 200 else second
    operation_id = winner.json()["operation_id"]
    finish = await client.post(
        f"/internal/operations/{operation_id}/finish",
        headers=headers,
        json={"state": "succeeded", "actual_amount": 100},
    )
    assert finish.status_code == 200
    usage = await client.get("/v1/me/usage", headers=app_headers(tokens))
    assert usage.json()["remaining"]["ai_tokens"] == 19900


async def test_idempotency_semantics(client, database) -> None:
    tokens = await register_and_login(
        client, database, "idem@example.com", "99999999-9999-4999-8999-999999999999"
    )
    headers = app_headers(tokens)
    created = await client.post(
        "/internal/operations/reserve", headers=headers, json=reserve_body("idem-key-1")
    )
    assert created.status_code == 200
    running = await client.post(
        "/internal/operations/reserve", headers=headers, json=reserve_body("idem-key-1")
    )
    assert running.status_code == 409 and running.json()["code"] == "operation_in_progress"
    conflict = await client.post(
        "/internal/operations/reserve", headers=headers, json=reserve_body("idem-key-1", "b" * 32)
    )
    assert conflict.status_code == 409 and conflict.json()["code"] == "idempotency_conflict"
    operation_id = created.json()["operation_id"]
    await client.post(
        f"/internal/operations/{operation_id}/finish",
        headers=headers,
        json={"state": "succeeded", "actual_amount": 10},
    )
    repeat = await client.post(
        "/internal/operations/reserve", headers=headers, json=reserve_body("idem-key-1")
    )
    assert repeat.status_code == 200
    assert repeat.json()["created"] is False and repeat.json()["result_available"] is False


async def test_operation_is_owner_scoped(client, database) -> None:
    owner = await register_and_login(
        client, database, "owner@example.com", "aaaaaaaa-1111-4111-8111-111111111111"
    )
    other = await register_and_login(
        client, database, "other@example.com", "bbbbbbbb-2222-4222-8222-222222222222"
    )
    created = await client.post(
        "/internal/operations/reserve", headers=app_headers(owner), json=reserve_body("owner-key-1")
    )
    operation_id = created.json()["operation_id"]
    response = await client.get(
        f"/v1/operations/{operation_id}",
        headers={
            "Authorization": f"Bearer {other['access_token']}",
            "X-Session-Source": other["source"],
        },
    )
    assert response.status_code == 404


async def test_purchase_then_refund_revokes_paid_permission(client, database) -> None:
    tokens = await register_and_login(
        client, database, "billing@example.com", "cccccccc-3333-4333-8333-333333333333"
    )
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Session-Source": tokens["source"],
    }
    purchase = await client.post(
        "/v1/billing/purchases/verify",
        headers=headers,
        json={"product_id": "diary_plus_monthly", "purchase_token": "diary_plus_monthly:refund01"},
    )
    assert purchase.status_code == 200 and purchase.json()["plan_code"] == "plus"
    decision = await client.post(
        "/internal/authorize",
        headers={**headers, **INTERNAL},
        json={"permission": "memory:timeline"},
    )
    assert decision.status_code == 200 and decision.json()["allowed"] is True
    consumed = await client.post(
        "/internal/usage/consume",
        headers={**headers, **INTERNAL},
        json={"metric": "memory_calls", "amount": 1},
    )
    assert consumed.status_code == 204
    event = {
        "event_id": "evt-refund-1",
        "event_type": "refund",
        "purchase_token": "diary_plus_monthly:refund01",
        "product_id": "diary_plus_monthly",
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    body = json.dumps(event).encode()
    from identity.config.settings import get_settings

    signature = hmac.new(
        get_settings().source_encryption_key.encode(), body, hashlib.sha256
    ).hexdigest()
    webhook_headers = {"X-Fake-Signature": signature, "content-type": "application/json"}
    first = await client.post("/v1/billing/webhooks/fake", headers=webhook_headers, content=body)
    assert first.status_code == 200 and first.json()["status"] == "refunded"
    duplicate = await client.post(
        "/v1/billing/webhooks/fake", headers=webhook_headers, content=body
    )
    assert duplicate.status_code == 200 and duplicate.json()["status"] == "duplicate"
    after = await client.post(
        "/internal/authorize",
        headers={**headers, **INTERNAL},
        json={"permission": "memory:timeline"},
    )
    assert after.json()["allowed"] is False
