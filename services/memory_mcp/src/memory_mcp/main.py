"""Internal MCP memory ASGI application with service-token protection."""

from __future__ import annotations

import hmac
from contextlib import asynccontextmanager

from diary_observability import (
    configure_logging,
    install_error_handlers,
    render,
    request_context,
)
from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from memory_mcp.adapters.mcp.server import TRANSPORT_SECURITY, build_server
from memory_mcp.bootstrap import build_container
from memory_mcp.settings import get_settings


def create_app() -> FastAPI:
    """Compose the MCP server and minimal operational endpoints."""
    settings = get_settings()
    configure_logging("memory_mcp", settings.service_version)
    container = build_container(settings)
    server = build_server(container)
    mcp_app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=TRANSPORT_SECURITY,
        max_request_body_size=2 * 1024 * 1024,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await container.sink.start()
        async with server.session_manager.run():
            try:
                yield
            finally:
                await container.sink.close()

    app = FastAPI(title="Diary Memory MCP", version=settings.service_version, lifespan=lifespan)
    app.state.container = container
    app.middleware("http")(request_context)
    install_error_handlers(app)

    @app.middleware("http")
    async def service_auth(request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            header = request.headers.get("authorization", "")
            expected = f"Bearer {settings.mcp_service_token}"
            if not hmac.compare_digest(header, expected):
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        """Process liveness."""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready() -> dict[str, str]:
        """The service has no essential external persistence."""
        return {"status": "ready"}

    @app.get("/metrics")
    async def metrics(x_metrics_token: str = Header(default="")) -> Response:
        """Internal metrics."""
        expected = settings.metrics_token
        if not expected or x_metrics_token != expected:
            return JSONResponse({"detail": "not found"}, 404)
        return PlainTextResponse(render(), media_type="text/plain; version=0.0.4")

    app.mount("/", mcp_app)
    return app


app = create_app()
