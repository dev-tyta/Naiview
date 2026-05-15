"""FastAPI application entry point.

Owner: Aaliyah
See §13 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from naijareview.api.middleware import RequestIDMiddleware
from naijareview.api.routes import admin, health, task_a, task_b
from naijareview.api.routes.auth import router as auth_router
from naijareview.config import settings
from naijareview.db.engine import create_db_and_tables

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="NaijaReview Intelligence",
        description=("Review generation & recommendation API with optional Nigerian cultural mode"),
        version="0.1.0",
        debug=settings.api_debug,
    )

    # ─── Middleware ────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    # ─── Routes ───────────────────────────────────
    app.include_router(health.router, tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(task_a.router, prefix="/task-a", tags=["Task A"])
    app.include_router(task_b.router, prefix="/task-b", tags=["Task B"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])

    # ─── Exception handlers ───────────────────────

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        logger.warning("validation_error", errors=exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=str(request.url.path))
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": type(exc).__name__,
            },
        )

    # ─── Startup event ────────────────────────────

    @app.on_event("startup")
    async def startup() -> None:
        create_db_and_tables()
        logger.info(
            "NaijaReview API starting",
            port=settings.api_port,
            debug=settings.api_debug,
            cache_backend=settings.cache_backend,
        )

    return app


app = create_app()
