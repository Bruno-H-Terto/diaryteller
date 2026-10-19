"""Real MongoDB sink integration test with a content canary."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import pytest
from diary_observability import MongoLogSink, sanitize
from pymongo import AsyncMongoClient

pytestmark = pytest.mark.integration


async def test_sink_writes_only_sanitized_fields() -> None:
    url = os.environ.get("TEST_MONGO_URL", "mongodb://localhost:57017")
    client = AsyncMongoClient(url, serverSelectionTimeoutMS=2000)
    try:
        await client.admin.command("ping")
    except Exception as exc:
        await client.close()
        pytest.skip(f"MongoDB unavailable: {type(exc).__name__}")
    database = f"diary_test_{os.getpid()}"
    sink = MongoLogSink(
        url=url,
        database=database,
        service="test",
        environment="test",
        buffer_size=50,
    )
    await sink.start()
    marker = datetime.now(UTC).isoformat()
    sink.emit({"event": "test_event", "request_id": marker, "prompt": "CANARY-DIARY"})
    document = None
    for _ in range(50):
        await asyncio.sleep(0.1)
        document = await client[database]["events"].find_one({"request_id": marker})
        if document is not None:
            break
    assert document is not None
    assert "prompt" not in document
    assert "CANARY-DIARY" not in repr(document)
    assert set(document).issubset(
        set(sanitize(document)) | {"_id", "service", "environment", "timestamp"}
    )
    await sink.close()
    await client.drop_database(database)
    await client.close()
