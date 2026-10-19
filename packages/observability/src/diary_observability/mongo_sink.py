"""Bounded, non-blocking MongoDB sink for sanitized operational logs.

The buffer never grows beyond `buffer_size`; excess records are counted and
discarded. MongoDB availability never blocks request processing or streams.
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime
from typing import Any

from pymongo import AsyncMongoClient

from .sanitizer import sanitize


class MongoLogSink:
    """Deliver sanitized log documents from a bounded in-memory queue."""

    def __init__(
        self,
        *,
        url: str,
        database: str,
        service: str,
        environment: str,
        buffer_size: int = 1000,
        ttl_days: int = 7,
    ) -> None:
        self._url = url
        self._database = database
        self._service = service
        self._environment = environment
        self._ttl_days = ttl_days
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=buffer_size)
        self._client: AsyncMongoClient | None = None
        self._task: asyncio.Task[None] | None = None
        self._index_task: asyncio.Task[None] | None = None
        self._closed = False
        self.dropped = 0
        self._failed_batches = 0

    async def start(self) -> None:
        """Create the client and background consumer; never raises on Mongo down."""
        self._client = AsyncMongoClient(self._url, tz_aware=True, serverSelectionTimeoutMS=1500)
        self._task = asyncio.create_task(self._consume(), name="mongo-log-sink")
        self._index_task = asyncio.create_task(self._ensure_index(), name="mongo-log-index")

    async def _ensure_index(self) -> None:
        try:
            collection = self._client[self._database]["events"] if self._client else None
            if collection is not None:
                await collection.create_index(
                    "timestamp", expireAfterSeconds=self._ttl_days * 86400
                )
        except Exception:
            self._failed_batches += 1

    def emit(self, fields: dict[str, Any]) -> None:
        """Enqueue one record or count a drop when the buffer is full/closed."""
        if self._closed:
            self.dropped += 1
            return
        document = sanitize(fields)
        document.setdefault("timestamp", datetime.now(UTC))
        document.setdefault("service", self._service)
        document.setdefault("environment", self._environment)
        try:
            self._queue.put_nowait(document)
        except asyncio.QueueFull:
            self.dropped += 1

    async def _consume(self) -> None:
        while True:
            first = await self._queue.get()
            batch = [first]
            while len(batch) < 100:
                try:
                    batch.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            if self._client is None:
                self.dropped += len(batch)
                continue
            try:
                await self._client[self._database]["events"].insert_many(batch, ordered=False)
                self._failed_batches = 0
            except Exception:
                self.dropped += len(batch)
                self._failed_batches += 1
                await asyncio.sleep(min(2.0, 0.1 * (2**self._failed_batches)))
            finally:
                for _ in batch:
                    self._queue.task_done()

    async def close(self, flush_timeout: float = 2.0) -> None:
        """Stop accepting records and make a bounded attempt to flush."""
        self._closed = True
        if self._task is not None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._queue.join(), timeout=flush_timeout)
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._index_task is not None:
            self._index_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._index_task
        if self._client is not None:
            await self._client.close()
