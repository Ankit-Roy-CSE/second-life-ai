"""
FastAPI application factory for all Amazon Second Life AI services.

Usage (in each service's app/main.py):

    from shared_py.web import create_app

    app = create_app(service_name="grading")

    # Optionally wire additional routes and lifespan logic:
    from shared_py.web import create_app
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app):
        # startup: init DB engine, Redis pool, event consumers …
        yield
        # shutdown: close connections …

    app = create_app(service_name="grading", lifespan=lifespan)
    app.include_router(my_router, prefix="/grades")

What create_app() wires automatically:
    - Structured JSON logging (via shared_py.config)
    - CORS (origins from CORS_ORIGINS env var, default: http://localhost:3000)
    - CorrelationIdMiddleware + RequestLoggingMiddleware
    - GET /health  (liveness)
    - GET /ready   (readiness — services add their own checks via add_ready_check())
    - AppError handler  → ErrorEnvelope JSON
    - HTTPException handler → ErrorEnvelope JSON
    - RequestValidationError handler → ErrorEnvelope JSON
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared_py.config import configure_logging
from shared_py.config.settings import BaseServiceSettings
from shared_py.web.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    validation_exception_handler,
)
from shared_py.web.health import add_ready_check, set_service_name
from shared_py.web.health import router as health_router
from shared_py.web.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware


@asynccontextmanager
async def _default_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: RUF029
    """No-op lifespan used when the service doesn't provide one."""
    yield


def create_app(
    service_name: str,
    *,
    lifespan: Any | None = None,
    settings: BaseServiceSettings | None = None,
    title: str | None = None,
    version: str = "0.1.0",
) -> FastAPI:
    """
    Build and return a configured FastAPI application.

    Args:
        service_name: Short identifier, e.g. "grading". Used in logs,
                      health responses, and OpenAPI metadata.
        lifespan:     Optional async context manager for startup/shutdown.
                      Receives the FastAPI app instance.
        settings:     Optional pre-constructed settings object. When omitted,
                      a BaseServiceSettings is instantiated from env vars.
        title:        OpenAPI title; defaults to "Second Life AI — <service_name>".
        version:      OpenAPI version string.

    Returns:
        A fully configured FastAPI app ready for `uvicorn app.main:app`.
    """
    if settings is None:
        settings = BaseServiceSettings(service_name=service_name)

    # Configure structured logging first so all subsequent imports can log
    configure_logging(service_name=service_name, level=settings.log_level)

    # Register service name for health responses
    set_service_name(service_name)
    # Build app
    app = FastAPI(
        title=title or f"Second Life AI — {service_name}",
        version=version,
        lifespan=lifespan or _default_lifespan,
        # Disable default exception handlers — we register our own below
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Middleware (outermost first) ──────────────────────────────────────────
    # CORS must be added before logging/correlation so it can handle preflight
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-correlation-id"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

    # ── Built-in routes ───────────────────────────────────────────────────────
    app.include_router(health_router)

    return app
