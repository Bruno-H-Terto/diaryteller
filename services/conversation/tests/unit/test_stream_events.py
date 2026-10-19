"""Cancellation and deadline behavior of the provider iterator."""

from __future__ import annotations

import asyncio

import pytest
from conversation.application.ports import TextDelta
from conversation.application.stream_events import (
    OperationCancelled,
    ProviderTimeout,
    cancel_aware,
)


async def source():
    yield TextDelta("a")
    yield TextDelta("b")


async def test_cancel_event_stops_iteration() -> None:
    cancel = asyncio.Event()
    cancel.set()
    with pytest.raises(OperationCancelled):
        async for _ in cancel_aware(
            source(),
            cancel,
            first_deadline=asyncio.get_running_loop().time() + 10,
            operation_deadline=asyncio.get_running_loop().time() + 10,
        ):
            pass


async def test_first_token_deadline_raises() -> None:
    cancel = asyncio.Event()

    async def slow():
        await asyncio.sleep(5)
        yield TextDelta("late")

    with pytest.raises(ProviderTimeout):
        async for _ in cancel_aware(
            slow(),
            cancel,
            first_deadline=asyncio.get_running_loop().time() + 0.05,
            operation_deadline=asyncio.get_running_loop().time() + 10,
        ):
            pass
