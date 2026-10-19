"""Android delta contract validation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from diary_contracts.context_ref import (
    ContextCreate,
    ContextPurpose,
    EventPrecision,
    RetentionPolicy,
    SelectedRecord,
)
from diary_contracts.conversation import ConversationRequest, ResponseMode
from diary_contracts.errors import ErrorCode, ErrorEnvelope
from diary_contracts.feed import ChangesPage, RemoteManifest, ResourceType, SnapshotPage
from diary_contracts.quota import QuotaAmount, UploadLimits, UploadQuota
from diary_contracts.result_contract import ConversationPayload, ResultView
from diary_contracts.upload import PartSignRequest, SignUrlsRequest, UploadComplete
from pydantic import ValidationError

HASH = "64d9e7ec35789a2dc00a857516f9dc86bea6c9835e17e3a9569421cdaf336f40"


def record(**overrides) -> SelectedRecord:
    values = {
        "local_record_id": uuid4(),
        "local_version_id": uuid4(),
        "local_version_number": 1,
        "base_local_version_id": None,
        "content_sha256": HASH,
        "text": "Hoje organizei minhas tarefas de trabalho.",
        "recorded_at": datetime(2026, 10, 19, 2, tzinfo=UTC),
        "event_at": None,
        "event_date": None,
        "event_description": None,
        "event_precision": EventPrecision.UNKNOWN,
        "timezone": "America/Sao_Paulo",
    }
    values.update(overrides)
    return SelectedRecord.model_validate(values)


def test_date_precision_requires_event_date() -> None:
    with pytest.raises(ValidationError):
        record(event_precision=EventPrecision.DATE)


def test_datetime_precision_requires_event_at() -> None:
    with pytest.raises(ValidationError):
        record(event_precision=EventPrecision.DATETIME)


def test_unknown_precision_rejects_dates() -> None:
    with pytest.raises(ValidationError):
        record(event_description="ontem")


def test_approximate_accepts_description() -> None:
    value = record(
        event_precision=EventPrecision.APPROXIMATE,
        event_description="por volta daquela semana",
    )
    assert value.event_precision is EventPrecision.APPROXIMATE


def test_invalid_timezone_is_rejected() -> None:
    with pytest.raises(ValidationError):
        record(timezone="Mars/Olympus")


def test_transcription_context_starts_empty() -> None:
    with pytest.raises(ValidationError):
        ContextCreate(
            client_context_id=uuid4(),
            purpose=ContextPurpose.TRANSCRIBE,
            retention_policy=RetentionPolicy.DELETE_AFTER_PROCESSING,
            records=[record()],
        )


def test_retention_has_no_default() -> None:
    with pytest.raises(ValidationError):
        ContextCreate(  # type: ignore[call-arg]
            client_context_id=uuid4(), purpose=ContextPurpose.CONVERSATION, records=[]
        )


def test_context_id_and_inline_context_are_exclusive() -> None:
    payload = {
        "client_message_id": str(uuid4()),
        "conversation_id": str(uuid4()),
        "context_id": str(uuid4()),
        "mode": "conversation",
        "message": "oi",
        "context": {
            "records": [
                {
                    "id": "r1",
                    "recorded_at": datetime.now(UTC).isoformat(),
                    "text": "x",
                }
            ]
        },
    }
    with pytest.raises(ValidationError):
        ConversationRequest.model_validate(payload)


def test_memory_mode_accepts_context_id() -> None:
    value = ConversationRequest.model_validate(
        {
            "client_message_id": str(uuid4()),
            "conversation_id": str(uuid4()),
            "context_id": str(uuid4()),
            "mode": "timeline",
            "message": "organize",
        }
    )
    assert value.context_id is not None


def test_checksum_base64_length_is_enforced() -> None:
    with pytest.raises(ValidationError):
        PartSignRequest(part_number=1, checksum_sha256_base64="short")
    parts = SignUrlsRequest(parts=[PartSignRequest(part_number=1, checksum_sha256_base64="A" * 44)])
    assert parts.parts[0].part_number == 1


def test_complete_requires_part_etag() -> None:
    with pytest.raises(ValidationError):
        UploadComplete.model_validate({"parts": [{"part_number": 1, "etag": ""}]})


def test_result_payload_is_discriminated() -> None:
    payload = ConversationPayload(answer="ok", coverage="selected_context", warnings=[])
    result = ResultView(
        result_id=uuid4(),
        operation_id=uuid4(),
        context_id=uuid4(),
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC),
        payload_sha256=HASH,
        payload=payload,
    )
    assert result.payload.kind == "conversation"


def test_error_envelope_exposes_message() -> None:
    envelope = ErrorEnvelope(
        type="https://diary.local/errors/quota",
        title="Quota",
        message="Quota",
        status=429,
        code=ErrorCode.DAILY_UPLOAD_BYTES_EXCEEDED,
        request_id="r" * 8,
    )
    assert envelope.message == envelope.title


def test_snapshot_and_changes_shapes() -> None:
    changes = ChangesPage(changes=[], next_cursor=None, has_more=False)
    assert changes.changes == []
    manifest = RemoteManifest(
        resource_type=ResourceType.CONTEXT,
        resource_id=uuid4(),
        revision=1,
        state="READY",
        expires_at=None,
    )
    page = SnapshotPage(items=[manifest], next_cursor=None, has_more=False, resume_cursor=None)
    assert page.items[0].state == "READY"


def test_upload_quota_requires_all_metrics() -> None:
    amount = QuotaAmount(used=0, reserved=0, limit=1, remaining=1)
    quota = UploadQuota(
        tier="free",
        window_start=datetime.now(UTC),
        reset_at=datetime.now(UTC),
        daily_upload_count=amount,
        daily_upload_bytes=amount,
        retained_storage_bytes=amount,
        **UploadLimits(
            max_file_bytes=1,
            max_context_bytes=1,
            max_context_records=50,
            max_audio_seconds=120,
            max_concurrent_uploads=2,
        ).model_dump(),
    )
    assert quota.tier == "free"


def test_mode_enum_is_lowercase_for_legacy_api() -> None:
    assert ResponseMode.CONVERSATION.value == "conversation"
