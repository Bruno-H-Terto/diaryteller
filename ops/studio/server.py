"""Serves the studio panel and the probes it needs: app bridge, stack, i18n.

Development only. Bind it to loopback; it exposes local diary text and the
development database to whoever can reach the port.
"""

from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

NO_CACHE = {"Cache-Control": "no-store"}

from .backend import rows as backend_rows
from .backend import tables as backend_tables
from .catalogues import summary
from .config import CATALOGUES, STATIC, Settings
from .device import BridgeUnavailable, DeviceBridge

settings = Settings.load()
bridge = DeviceBridge(settings.bridge_url)
app = FastAPI(title="Diaryteller studio", docs_url=None, redoc_url=None)


@app.get("/")
async def index() -> FileResponse:
    """Serve the single-page panel."""
    return FileResponse(STATIC / "panel.html", headers=NO_CACHE)


@app.get("/panel.js")
async def script() -> FileResponse:
    """Serve the panel script."""
    return FileResponse(STATIC / "panel.js", media_type="text/javascript", headers=NO_CACHE)


@app.get("/panel-data.js")
async def data_script() -> FileResponse:
    """Serve the data views of the panel."""
    return FileResponse(STATIC / "panel-data.js", media_type="text/javascript", headers=NO_CACHE)


@app.get("/panel.css")
async def style() -> FileResponse:
    """Serve the panel stylesheet."""
    return FileResponse(STATIC / "panel.css", media_type="text/css", headers=NO_CACHE)


@app.get("/api/status")
async def status() -> dict:
    """Report the app bridge and every stack service in one call."""
    services = []
    async with httpx.AsyncClient(timeout=2.5) as client:
        for service in settings.services:
            services.append({**service, **await probe(client, service["probe"])})
    app_state = await probe_app()
    return {"app": app_state, "services": services, "bridge": settings.bridge_url}


async def probe(client: httpx.AsyncClient, url: str) -> dict:
    """Check one service without failing the whole panel."""
    try:
        response = await client.get(url)
        return {"up": response.status_code < 500, "code": response.status_code}
    except httpx.HTTPError:
        return {"up": False, "code": None}


async def probe_app() -> dict:
    """Check the on-device bridge."""
    try:
        return {"up": True, **(await bridge.health())}
    except BridgeUnavailable as error:
        return {"up": False, "error": str(error)}


@app.get("/api/app")
async def app_state() -> JSONResponse:
    """Mirror the local diary state the app holds right now."""
    try:
        return JSONResponse(await bridge.state())
    except BridgeUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/app/entities/{entity_id}")
async def update_entity(entity_id: str, payload: dict) -> dict:
    """Change a name or avatar description; the app re-renders immediately."""
    try:
        return await bridge.update_entity(entity_id, payload)
    except BridgeUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/app/pins")
async def pin(payload: dict) -> dict:
    """Persist one dragged map position in the app database."""
    try:
        return await bridge.pin(payload["entityId"], float(payload["x"]), float(payload["y"]))
    except BridgeUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail="entityId, x and y are required") from error


@app.post("/api/app/pins/reset")
async def reset_pins() -> dict:
    """Return the map to the default ring."""
    try:
        return await bridge.clear_pins()
    except BridgeUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/backend/tables")
async def tables() -> dict:
    """List backend tables so the panel can browse the stack state."""
    try:
        return {"tables": await backend_tables(settings.database_url)}
    except Exception as error:  # noqa: BLE001 - the panel shows the stack as offline
        return {"tables": [], "error": str(error)}


@app.get("/api/backend/tables/{table}")
async def table_rows(table: str) -> dict:
    """Return the rows of one allowlisted backend table."""
    listed = {item["name"] for item in await backend_tables(settings.database_url)}
    try:
        return {"table": table, "rows": await backend_rows(settings.database_url, table, listed)}
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/i18n")
async def i18n() -> dict:
    """Show every language file and the keys it still misses."""
    return summary(Path(CATALOGUES))
