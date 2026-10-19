"""Authorized context copies: create idempotently, seal, and read by owner."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime

from diary_contracts.context_ref import (
    ContextCreate,
    ContextState,
    ContextView,
    RetentionUpdate,
    SelectedRecord,
)
from diary_contracts.errors import DomainError, ErrorCode

from exchange.application.crypto import open_payload, seal_payload
from exchange.application.ports.contexts import ContextRepository
from exchange.application.ports.storage import BlobStore
from exchange.domain.context import ContextCopy, ContextSource

from .views import context_view

ETAG_PATTERN = re.compile(r'^(?:W/)?"?ctx-(\d+)"?$')


def _not_found() -> DomainError:
    return DomainError(ErrorCode.NOT_FOUND, 404, "Context not found")


def _storage_key(owner_id: uuid.UUID, context_id: uuid.UUID) -> str:
    return f"contexts/{owner_id}/{context_id}.json.enc"


async def create_context(
    *,
    owner_id: uuid.UUID,
    body: ContextCreate,
    contexts: ContextRepository,
    blobs: BlobStore,
    master_key: str,
    max_bytes: int,
    now: datetime,
) -> tuple[ContextView, bool]:
    """Create the copy once per `client_context_id`; retries return the same row."""
    if body.text_bytes > max_bytes:
        raise DomainError(
            ErrorCode.CONTEXT_TOO_LARGE,
            413,
            "Selected records exceed the context limit",
            details={"limit_bytes": max_bytes, "requested_bytes": body.text_bytes},
        )
    existing = await contexts.by_client_id(owner_id, body.client_context_id)
    if existing is not None:
        return await _reload(existing, contexts), False
    context_id = uuid.uuid4()
    payload = {
        "client_context_id": str(body.client_context_id),
        "purpose": body.purpose.value,
        "records": [record.model_dump(mode="json") for record in body.records],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    sealed = seal_payload(master_key, context_id, payload)
    key = _storage_key(owner_id, context_id)
    await blobs.put(key, sealed)
    copy = ContextCopy(
        id=context_id,
        owner_id=owner_id,
        client_context_id=body.client_context_id,
        state=ContextState.DRAFT,
        purpose=body.purpose,
        retention_policy=body.retention_policy,
        revision=1,
        created_at=now,
        updated_at=now,
        expires_at=None,
        storage_key=key,
        content_sha256=hashlib.sha256(canonical).hexdigest(),
        record_count=len(body.records),
        text_bytes=body.text_bytes,
        deletion_id=None,
    )
    sources = [
        ContextSource(
            context_id=context_id,
            local_record_id=record.local_record_id,
            local_version_id=record.local_version_id,
            content_sha256=record.content_sha256,
        )
        for record in body.records
    ]
    if not await contexts.create(copy, sources):
        await blobs.delete(key)
        raced = await contexts.by_client_id(owner_id, body.client_context_id)
        if raced is None:
            raise DomainError(ErrorCode.IDEMPOTENCY_CONFLICT, 409, "Context creation conflicted")
        return await _reload(raced, contexts), False
    return context_view(copy, sources), True


async def _reload(copy: ContextCopy, contexts: ContextRepository) -> ContextView:
    return context_view(copy, await contexts.sources(copy.id))


async def get_context(
    *, owner_id: uuid.UUID, context_id: uuid.UUID, contexts: ContextRepository
) -> ContextView:
    """Return the owner's manifest; deleted copies are gone."""
    copy = await contexts.by_id(owner_id, context_id)
    if copy is None or copy.state is ContextState.DELETED:
        raise _not_found()
    return await _reload(copy, contexts)


async def update_retention(
    *,
    owner_id: uuid.UUID,
    context_id: uuid.UUID,
    body: RetentionUpdate,
    expected_revision: int | None,
    contexts: ContextRepository,
    now: datetime,
) -> ContextView:
    """Apply `If-Match` and return the new revision."""
    if expected_revision is None:
        raise DomainError(
            ErrorCode.PRECONDITION_REQUIRED, 428, "If-Match with the current revision is required"
        )
    updated = await contexts.update_retention(
        owner_id, context_id, body.retention_policy, expected_revision, now
    )
    if updated is None:
        current = await contexts.by_id(owner_id, context_id)
        if current is None:
            raise _not_found()
        if current.state in {ContextState.DELETE_PENDING, ContextState.DELETED}:
            raise DomainError(ErrorCode.CONTEXT_NOT_READY, 409, "Context is being deleted")
        raise DomainError(ErrorCode.PRECONDITION_FAILED, 412, "Revision does not match")
    return await _reload(updated, contexts)


async def seal_context(
    *,
    owner_id: uuid.UUID,
    context_id: uuid.UUID,
    contexts: ContextRepository,
    now: datetime,
) -> ContextView:
    """Freeze the copy; repeating the call does not create a revision."""
    sealed = await contexts.seal(owner_id, context_id, now)
    if sealed is None:
        raise _not_found()
    if sealed.state is not ContextState.READY:
        raise DomainError(ErrorCode.CONTEXT_NOT_READY, 409, "Context cannot be sealed yet")
    return await _reload(sealed, contexts)


async def read_records(
    *,
    owner_id: uuid.UUID,
    context_id: uuid.UUID,
    contexts: ContextRepository,
    blobs: BlobStore,
    master_key: str,
) -> list[SelectedRecord]:
    """Decrypt records for a trusted service or the owner."""
    copy = await contexts.by_id(owner_id, context_id)
    if copy is None or copy.state is ContextState.DELETED:
        raise _not_found()
    if copy.state is not ContextState.READY:
        raise DomainError(ErrorCode.CONTEXT_NOT_READY, 409, "Context is not ready")
    payload = open_payload(master_key, copy.id, await blobs.get(copy.storage_key))
    records = payload.get("records")
    if not isinstance(records, list):
        raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Stored context is invalid")
    try:
        return [SelectedRecord.model_validate(record) for record in records]
    except ValueError as exc:
        raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Stored context is invalid") from exc


def parse_etag(value: str | None) -> int | None:
    """Extract the revision from a weak or strong ETag."""
    if not value:
        return None
    match = ETAG_PATTERN.match(value.strip())
    return int(match.group(1)) if match else None
