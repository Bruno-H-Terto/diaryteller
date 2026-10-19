"""Context copy lifecycle: create, seal, retention and deletion."""

from __future__ import annotations

import uuid

import pytest
from support import principal_for

pytestmark = pytest.mark.integration

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
HEADERS = {"Authorization": "Bearer token", "X-Session-Source": "source"}
INTERNAL = {"X-Internal-Service": "conversation", "X-Internal-Token": "test-conversation"}


def context_body(client_id: str | None = None, text: str = "Primeiro dia") -> dict:
    """Build a valid context creation payload."""
    return {
        "client_context_id": client_id or str(uuid.uuid4()),
        "purpose": "conversation",
        "retention_policy": "delete_after_processing",
        "records": [
            {
                "local_record_id": str(uuid.uuid4()),
                "local_version_id": str(uuid.uuid4()),
                "local_version_number": 1,
                "base_local_version_id": None,
                "content_sha256": "a" * 64,
                "text": text,
                "recorded_at": "2026-10-19T10:00:00+00:00",
                "event_at": "2026-10-18T21:00:00+00:00",
                "event_date": None,
                "event_description": None,
                "event_precision": "datetime",
                "timezone": "America/Sao_Paulo",
            }
        ],
    }


async def _create(client, body: dict) -> dict:
    response = await client.post("/v1/exchange/contexts", json=body, headers=HEADERS)
    assert response.status_code in {200, 201}, response.text
    return response.json()


async def test_create_and_read_manifest(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    created = await client.post("/v1/exchange/contexts", json=context_body(), headers=HEADERS)
    assert created.status_code == 201, created.text
    assert created.headers["etag"] == '"ctx-1"'
    assert created.headers["location"].startswith("/v1/exchange/contexts/")
    body = created.json()
    assert body["state"] == "DRAFT"
    assert len(body["sources"]) == 1
    read = await client.get(f"/v1/exchange/contexts/{body['context_id']}", headers=HEADERS)
    assert read.status_code == 200
    assert read.json()["context_id"] == body["context_id"]
    assert authorizer.permissions == ["exchange:use", "exchange:use"]


async def test_create_is_idempotent_per_client_context_id(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    body = context_body()
    first = await client.post("/v1/exchange/contexts", json=body, headers=HEADERS)
    second = await client.post("/v1/exchange/contexts", json=body, headers=HEADERS)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["context_id"] == second.json()["context_id"]


async def test_text_is_encrypted_at_rest(client, authorizer, blobs) -> None:
    authorizer.principal = principal_for(OWNER)
    body = context_body(text="segredo absoluto")
    await client.post("/v1/exchange/contexts", json=body, headers=HEADERS)
    stored = next(iter(blobs.objects.values()))
    assert b"segredo absoluto" not in stored


async def test_seal_is_idempotent(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    view = await _create(client, context_body())
    sealed = await client.post(f"/v1/exchange/contexts/{view['context_id']}/seal", headers=HEADERS)
    assert sealed.status_code == 200
    assert sealed.json()["state"] == "READY"
    again = await client.post(f"/v1/exchange/contexts/{view['context_id']}/seal", headers=HEADERS)
    assert again.json()["revision"] == sealed.json()["revision"]


async def test_retention_requires_matching_etag(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    view = await _create(client, context_body())
    path = f"/v1/exchange/contexts/{view['context_id']}/retention"
    missing = await client.patch(
        path, json={"retention_policy": "keep_until_deleted"}, headers=HEADERS
    )
    assert missing.status_code == 428
    stale = await client.patch(
        path,
        json={"retention_policy": "keep_until_deleted"},
        headers={**HEADERS, "If-Match": '"ctx-9"'},
    )
    assert stale.status_code == 412
    updated = await client.patch(
        path,
        json={"retention_policy": "keep_until_deleted"},
        headers={**HEADERS, "If-Match": '"ctx-1"'},
    )
    assert updated.status_code == 200
    assert updated.json()["retention_policy"] == "keep_until_deleted"
    assert updated.json()["revision"] == 2


async def test_delete_is_durable_and_idempotent(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    view = await _create(client, context_body())
    path = f"/v1/exchange/contexts/{view['context_id']}"
    deleted = await client.delete(path, headers=HEADERS)
    assert deleted.status_code == 202
    deletion = deleted.json()
    assert deletion["state"] == "PENDING"
    again = await client.delete(path, headers=HEADERS)
    assert again.json()["deletion_id"] == deletion["deletion_id"]
    status = await client.get(f"/v1/exchange/deletions/{deletion['deletion_id']}", headers=HEADERS)
    assert status.status_code == 200
    assert status.json()["state"] == "PENDING"


async def test_context_is_owner_scoped(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    view = await _create(client, context_body())
    authorizer.principal = principal_for(OTHER)
    response = await client.get(f"/v1/exchange/contexts/{view['context_id']}", headers=HEADERS)
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_oversized_context_is_rejected(client, authorizer, monkeypatch) -> None:
    authorizer.principal = principal_for(OWNER)
    from exchange.app import app

    monkeypatch.setattr(app.state.container.settings, "context_max_bytes", 4)
    response = await client.post("/v1/exchange/contexts", json=context_body(), headers=HEADERS)
    assert response.status_code == 413
    assert response.json()["code"] == "context_too_large"


async def test_internal_records_require_service_token_and_ready_state(client, authorizer) -> None:
    authorizer.principal = principal_for(OWNER)
    view = await _create(client, context_body())
    path = f"/internal/contexts/{view['context_id']}?owner_id={OWNER}"
    denied = await client.get(path, headers={**INTERNAL, "X-Internal-Token": "wrong"})
    assert denied.status_code == 401
    not_ready = await client.get(path, headers=INTERNAL)
    assert not_ready.status_code == 409
    await client.post(f"/v1/exchange/contexts/{view['context_id']}/seal", headers=HEADERS)
    records = await client.get(path, headers=INTERNAL)
    assert records.status_code == 200
    payload = records.json()
    assert len(payload["records"]) == 1
    assert payload["records"][0]["text"] == "Primeiro dia"
