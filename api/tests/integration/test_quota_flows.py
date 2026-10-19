"""Upload quota visibility, reservations and capacity gauges."""

from __future__ import annotations

import pytest
from helpers import auth_headers, internal_headers, owner_and_tokens

pytestmark = pytest.mark.integration


async def test_quota_view_reports_free_fixtures(client, database) -> None:
    tokens, _ = await owner_and_tokens(
        client, database, "quota@example.com", "11111111-1111-4111-8111-111111111111"
    )
    response = await client.get("/v1/me/upload-quota", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tier"] == "free"
    assert body["daily_upload_count"]["limit"] == 5
    assert body["retained_storage_bytes"]["limit"] == 50 * 1024 * 1024
    assert body["max_concurrent_uploads"] == 2


async def test_reservation_commit_and_release(client, database) -> None:
    tokens, owner = await owner_and_tokens(
        client, database, "commit@example.com", "22222222-2222-4222-8222-222222222222"
    )
    reserved = await client.post(
        "/internal/upload-quota/reserve",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "daily_upload_count",
            "amount": 1,
            "reference": "upload-commit-1",
        },
    )
    assert reserved.status_code == 200, reserved.text
    view = reserved.json()
    assert view["reserved"] == 1 and view["remaining"] == 4
    again = await client.post(
        "/internal/upload-quota/reserve",
        headers=internal_headers(),
        json={
            "owner_id": owner,
            "metric": "daily_upload_count",
            "amount": 1,
            "reference": "upload-commit-1",
        },
    )
    assert again.json()["reservation_id"] == view["reservation_id"]
    commit = await client.post(
        "/internal/upload-quota/commit",
        headers=internal_headers(),
        json={"owner_id": owner, "reservation_id": view["reservation_id"]},
    )
    assert commit.status_code == 204
    quota = await client.get("/v1/me/upload-quota", headers=auth_headers(tokens))
    assert quota.json()["daily_upload_count"] == {
        "used": 1,
        "reserved": 0,
        "limit": 5,
        "remaining": 4,
    }
    release = await client.post(
        "/internal/upload-quota/release",
        headers=internal_headers(),
        json={"owner_id": owner, "reservation_id": view["reservation_id"]},
    )
    assert release.status_code == 204
    quota = await client.get("/v1/me/upload-quota", headers=auth_headers(tokens))
    assert quota.json()["daily_upload_count"]["used"] == 1
