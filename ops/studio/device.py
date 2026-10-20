"""Talks to the debug bridge that runs inside the app on the emulator/device.

The bridge is exposed by `adb forward tcp:5557 tcp:5557`; this client only sends
HTTP to loopback. When no device is attached every call fails fast so the panel
can show the app as offline instead of breaking.
"""

from __future__ import annotations

import httpx

TIMEOUT = httpx.Timeout(4.0)


class BridgeUnavailable(RuntimeError):
    """Raised when the app is not running or the forward is missing."""


class DeviceBridge:
    """Thin async client for the app's debugging surface."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def health(self) -> dict:
        """Return the bridge version document, or raise when offline."""
        return await self._call("GET", "/health")

    async def state(self) -> dict:
        """Return records, entities, events, links and manual map positions."""
        return await self._call("GET", "/state")

    async def update_entity(self, entity_id: str, payload: dict) -> dict:
        """Patch one entity name or avatar description."""
        return await self._call("POST", f"/entities/{entity_id}", json=payload)

    async def pin(self, entity_id: str, x: float, y: float) -> dict:
        """Store one manual map position, normalised to the ring radius."""
        return await self._call("POST", "/pins", json={"entityId": entity_id, "x": x, "y": y})

    async def clear_pins(self) -> dict:
        """Drop every manual position, returning the map to the default ring."""
        return await self._call("POST", "/pins/reset", json={})

    async def _call(self, method: str, path: str, json: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.request(method, url, json=json)
        except httpx.HTTPError as error:
            raise BridgeUnavailable(
                "app bridge offline: run `make app` (emulator + adb forward)",
            ) from error
        if response.status_code >= 400:
            raise BridgeUnavailable(
                f"bridge answered {response.status_code}: {response.text[:200]}"
            )
        return response.json()
