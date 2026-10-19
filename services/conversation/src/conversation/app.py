"""Conversation ASGI application and lifespan."""

from __future__ import annotations

from contextlib import asynccontextmanager

from diary_observability import (
    configure_logging,
    install_error_handlers,
    render,
    request_context,
)
from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from conversation.config.bootstrap import build_container
from conversation.config.container import Container
from conversation.config.settings import get_settings
from conversation.controllers.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the log sink and close HTTP/provider resources."""
    container: Container = app.state.container
    await container.sink.start()
    try:
        yield
    finally:
        await container.sink.close()
        await container.identity_http.aclose()


def create_app() -> FastAPI:
    """Compose the streaming service explicitly."""
    settings = get_settings()
    configure_logging("conversation", settings.service_version)
    app = FastAPI(
        title="Diary Conversation API", version=settings.service_version, lifespan=lifespan
    )
    app.state.container = build_container(settings)
    app.middleware("http")(request_context)
    install_error_handlers(app)
    app.include_router(router, prefix="/v1")

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        """Process liveness."""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready(request: Request) -> Response:
        """Require identity authorization; Mongo is not essential."""
        container: Container = request.app.state.container
        try:
            response = await container.identity_http.get(
                f"{container.settings.identity_internal_url}/health/ready", timeout=2.0
            )
            if response.status_code >= 500:
                raise RuntimeError("identity unavailable")
        except Exception:
            return JSONResponse({"status": "unavailable", "dependency": "identity"}, 503)
        return JSONResponse({"status": "ready"})

    @app.get("/metrics")
    async def metrics(x_metrics_token: str = Header(default="")) -> Response:
        """Internal metrics."""
        expected = settings.metrics_token
        if not expected or x_metrics_token != expected:
            return JSONResponse({"detail": "not found"}, 404)
        return PlainTextResponse(render(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()
