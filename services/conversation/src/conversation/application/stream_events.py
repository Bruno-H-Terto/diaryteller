"""Cancel-aware iteration over provider events with deadlines."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any


class OperationCancelled(Exception):
    """Cancellation requested by the user, revocation or shutdown."""


class ProviderTimeout(Exception):
    """Provider exceeded first-token or total deadline."""


async def cancel_aware(
    stream: Any,
    cancel: asyncio.Event,
    *,
    first_deadline: float,
    operation_deadline: float,
) -> AsyncIterator[Any]:
    """Yield provider events while racing cancellation and deadlines."""
    iterator = stream.__aiter__()
    first = True
    while True:
        if cancel.is_set():
            raise OperationCancelled()
        loop = asyncio.get_running_loop()
        limit = min(operation_deadline, first_deadline if first else operation_deadline)
        remaining = limit - loop.time()
        if remaining <= 0:
            raise ProviderTimeout()
        next_task = asyncio.create_task(anext(iterator))
        stop_task = asyncio.create_task(cancel.wait())
        done, _ = await asyncio.wait(
            {next_task, stop_task},
            timeout=remaining,
            return_when=asyncio.FIRST_COMPLETED,
        )
        stop_task.cancel()
        if not done:
            next_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, StopAsyncIteration):
                await next_task
            raise ProviderTimeout()
        if stop_task in done:
            next_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, StopAsyncIteration):
                await next_task
            raise OperationCancelled()
        try:
            event = next_task.result()
        except StopAsyncIteration:
            return
        from conversation.application.ports import TextDelta, ToolCallReady

        if isinstance(event, (TextDelta, ToolCallReady)):
            first = False
        yield event
