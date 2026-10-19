"""Speech ASGI application."""

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

from speech.adapters.http.synthesis_routes import router as synthesis_router
from speech.adapters.http.transcription_routes import router as transcription_router
from speech.bootstrap import build_container
from speech.container import Container
from speech.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start logging and close HTTP resources."""
    container: Container = app.state.container
    await container.sink.start()
    try:
        yield
    finally:
        await container.sink.close()
        await container.identity_http.aclose()


def create_app() -> FastAPI:
    """Compose speech routes and health checks."""
    settings = get_settings()
    configure_logging("speech", settings.service_version)
    app = FastAPI(title="Diary Speech API", version=settings.service_version, lifespan=lifespan)
    app.state.container = build_container(settings)
    app.middleware("http")(request_context)
    install_error_handlers(app)
    app.include_router(transcription_router, prefix="/v1")
    app.include_router(synthesis_router, prefix="/v1")

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        """Process liveness."""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready(request: Request) -> Response:
        """Require identity authorization for readiness."""
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
