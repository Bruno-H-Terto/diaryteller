"""Identity ASGI application and process lifespan."""

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

from identity.config.bootstrap import build_container
from identity.config.container import Container
from identity.config.settings import get_settings
from identity.controllers import (
    account_routes,
    auth_routes,
    billing_routes,
    email_routes,
    internal_quota_routes,
    internal_routes,
    monetization_routes,
    oidc_routes,
    operation_routes,
    quota_routes,
    session_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the log consumer and dispose resources on shutdown."""
    container: Container = app.state.container
    await container.sink.start()
    try:
        yield
    finally:
        await container.sink.close()
        if container.oidc_http is not None:
            await container.oidc_http.aclose()
        await container.engine.dispose()


def create_app() -> FastAPI:
    """Compose routers, middleware and error handling explicitly."""
    settings = get_settings()
    configure_logging("identity", settings.service_version)
    app = FastAPI(title="Diary Identity API", version=settings.service_version, lifespan=lifespan)
    app.state.container = build_container(settings)
    app.middleware("http")(request_context)
    install_error_handlers(app)
    app.include_router(auth_routes.router, prefix="/v1")
    app.include_router(email_routes.router, prefix="/v1")
    app.include_router(account_routes.router, prefix="/v1")
    app.include_router(session_routes.router, prefix="/v1")
    app.include_router(operation_routes.router, prefix="/v1")
    app.include_router(billing_routes.router, prefix="/v1")
    app.include_router(quota_routes.router, prefix="/v1")
    app.include_router(monetization_routes.router, prefix="/v1")
    app.include_router(oidc_routes.router, prefix="/v1")
    app.include_router(internal_routes.router)
    app.include_router(internal_quota_routes.router)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        """Process liveness without dependency checks."""
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready(request: Request) -> Response:
        """Require PostgreSQL; Mongo only carries operational logs."""
        try:
            async with request.app.state.container.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse({"status": "unavailable", "dependency": "postgres"}, 503)
        return JSONResponse({"status": "ready"})

    @app.get("/metrics")
    async def metrics(
        x_metrics_token: str = Header(default=""),
    ) -> Response:
        """Expose internal metrics only when a token is configured and matches."""
        expected = settings.metrics_token
        if not expected or x_metrics_token != expected:
            return JSONResponse({"detail": "not found"}, 404)
        return PlainTextResponse(render(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()


__all__ = ["app", "create_app", "current_request_id"]
