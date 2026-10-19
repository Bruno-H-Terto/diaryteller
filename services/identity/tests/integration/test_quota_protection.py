"""Exhaustion, capacity gauges and scope protection for upload quotas."""

from __future__ import annotations

import pytest
from helpers import internal_headers, owner_and_tokens

pytestmark = pytest.mark.integration


async def test_daily_count_exhaustion_returns_documented_error(client, database) -> None:
    _, owner = await owner_and_tokens(
        client, database, "exhaust@example.com", "33333333-3333-4333-8333-333333333333"
    )
    for index in range(5):
        response = await client.post(
            "/internal/upload-quota/reserve",
            headers=internal_headers(),
            json={
                "owner_id": owner,
                "metric": "daily_upload_count",
                "amount": 1,
                "reference": f"exhaust-{index}",
            },
        )
        assert response.status_code == 200, response.text
    exceeded = await client.post(
        "/internal/upload-quota/reserve",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "daily_upload_count",
            "amount": 1,
            "reference": "exhaust-over",
        },
    )
    assert exceeded.status_code == 429
    body = exceeded.json()
    assert body["code"] == "daily_upload_count_exceeded"
    assert body["details"]["limit"] == 5
    assert body["details"]["requested"] == 1


async def test_capacity_gauge_is_idempotent_and_released(client, database) -> None:
    _, owner = await owner_and_tokens(
        client, database, "gauge@example.com", "44444444-4444-4444-8444-444444444444"
    )
    first = await client.post(
        "/internal/upload-quota/acquire",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "concurrent_uploads",
            "amount": 1,
            "reference": "session-a",
        },
    )
    assert first.status_code == 204
    duplicate = await client.post(
        "/internal/upload-quota/acquire",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "concurrent_uploads",
            "amount": 1,
            "reference": "session-a",
        },
    )
    assert duplicate.status_code == 204
    second = await client.post(
        "/internal/upload-quota/acquire",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "concurrent_uploads",
            "amount": 1,
            "reference": "session-b",
        },
    )
    assert second.status_code == 204
    blocked = await client.post(
        "/internal/upload-quota/acquire",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "concurrent_uploads",
            "amount": 1,
            "reference": "session-c",
        },
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "upload_concurrency_exceeded"
    closed = await client.post(
        "/internal/upload-quota/close",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "concurrent_uploads",
            "amount": 1,
            "reference": "session-a",
        },
    )
    assert closed.status_code == 204
    retried = await client.post(
        "/internal/upload-quota/acquire",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "concurrent_uploads",
            "amount": 1,
            "reference": "session-c",
        },
    )
    assert retried.status_code == 204


async def test_reservation_is_owner_scoped(client, database) -> None:
    _, first = await owner_and_tokens(
        client, database, "owner-a@example.com", "55555555-5555-4555-8555-555555555555"
    )
    _, second = await owner_and_tokens(
        client, database, "owner-b@example.com", "66666666-6666-4666-8666-666666666666"
    )
    reserved = await client.post(
        "/internal/upload-quota/reserve",
        headers=internal_headers(),
        json={
            "owner_id": first,
            "metric": "retained_storage_bytes",
            "amount": 1024,
            "reference": "owner-a-ref",
        },
    )
    assert reserved.status_code == 200, reserved.text
    stolen = await client.post(
        "/internal/upload-quota/commit",
        headers=internal_headers(),
        json={"owner_id": second, "reservation_id": reserved.json()["reservation_id"]},
    )
    assert stolen.status_code == 409
    assert stolen.json()["code"] == "upload_state_invalid"


async def test_internal_quota_requires_service_token(client, database) -> None:
    response = await client.post(
        "/internal/upload-quota/reserve",
        headers=internal_headers(token="wrong"),
        json={
            "owner_id": "77777777-7777-4777-8777-777777777777",
            "metric": "daily_upload_count",
            "amount": 1,
            "reference": "unauthorized-1",
        },
    )
    assert response.status_code == 401
