"""SSE framing with heartbeats and sequence numbers."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncGenerator
from uuid import UUID

from diary_contracts.stream import StreamEvent, StreamEventType, encode_comment, encode_sse

from conversation.models.response import ResponseEvent


async def event_stream(
    operation_id: UUID,
    events: AsyncGenerator[ResponseEvent, None],
    heartbeat_seconds: int,
) -> AsyncGenerator[str, None]:
    """Encode application events, emitting comments while the provider is idle."""
    sequence = 0
    pending: asyncio.Task | None = None
    try:
        while True:
            if pending is None:
                pending = asyncio.create_task(anext(events))
            heartbeat = asyncio.create_task(asyncio.sleep(heartbeat_seconds))
            done, _ = await asyncio.wait(
                {pending, heartbeat},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if heartbeat in done and pending not in done:
                yield encode_comment()
                continue
            heartbeat.cancel()
            try:
                event = pending.result()
            except StopAsyncIteration:
                break
            pending = None
            yield encode_sse(
                StreamEvent(
                    operation_id=operation_id,
                    sequence=sequence,
                    type=event.type,
                    data=event.data,
                )
            )
            sequence += 1
            if event.type in {StreamEventType.ERROR, StreamEventType.COMPLETED}:
                break
    finally:
        if pending is not None:
            pending.cancel()
            with contextlib.suppress(asyncio.CancelledError, StopAsyncIteration):
                await pending
        with contextlib.suppress(Exception):
            await events.aclose()
