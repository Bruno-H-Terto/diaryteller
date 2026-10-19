"""Periodic session/cancellation check during a long stream."""

from __future__ import annotations

import asyncio

from conversation.config.settings import Settings
from conversation.lib.ports import IdentityPort
from conversation.services.prepare import PreparedOperation


async def monitor_control(
    identity: IdentityPort,
    prepared: PreparedOperation,
    cancel: asyncio.Event,
    settings: Settings,
) -> None:
    """Stop the stream after revocation or a cancel request."""
    while True:
        await asyncio.sleep(settings.revalidate_seconds)
        try:
            control = await identity.control(prepared.auth, prepared.operation_id)
        except Exception:
            cancel.set()
            return
        if control.cancel_requested or not control.session_active:
            cancel.set()
            return
        if control.state in {"cancelled", "failed", "interrupted", "succeeded"}:
            cancel.set()
            return
