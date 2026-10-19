"""Exchange ASGI application and process lifespan."""

from __future__ import annotations

from contextlib import asynccontextmanager

from diary_observability import (
    configure_logging,
    current_request_id,
    install_error_handlers,
    render,
    request_context,
)
from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from exchange.config.bootstrap import build_container
from exchange.config.container import Container
from exchange.config.settings import get_settings
from exchange.controllers import context_routes, internal_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the log consumer and dispose resources on shutdown."""
    container: Container = app.state.container
    await container.sink.start()
    try:
        yield
    finally:
        await container.sink.close()
        await container.http.aclose()
        await container.engine.dispose()


def create_app() -> FastAPI:
    """Compose routers, middleware and error handling explicitly."""
    settings = get_settings()
    configure_logging("exchange", settings.service_version)
    app = FastAPI(title="Diary Exchange API", version=settings.service_version, lifespan=lifespan)
    app.state.container = build_container(settings)
    app.middleware("http")(request_context)
    install_error_handlers(app)
    app.include_router(context_routes.router, prefix="/v1")
    app.include_router(internal_routes.router)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        """Process liveness without dependency checks."""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready(request: Request) -> Response:
        """Require PostgreSQL; storage is checked by the upload flow."""
        try:
            async with request.app.state.container.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse({"status": "unavailable", "dependency": "postgres"}, 503)
        return JSONResponse({"status": "ready"})

    @app.get("/metrics")
    async def metrics(x_metrics_token: str = Header(default="")) -> Response:
        """Expose internal metrics only with a configured token."""
        expected = settings.metrics_token
        if not expected or x_metrics_token != expected:
            return JSONResponse({"detail": "not found"}, 404)
        return PlainTextResponse(render(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()


__all__ = ["app", "create_app", "current_request_id"]
