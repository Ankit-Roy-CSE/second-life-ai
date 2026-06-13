"""
Health and readiness endpoints shared by all services.

GET /health  — liveness probe (always 200 if the process is alive)
GET /ready   — readiness probe (checks DB + Redis connectivity)

Services that have additional dependencies can extend the readiness check
by calling add_ready_check() in their lifespan:

    from shared_py.web.health import add_ready_check

    async def check_db() -> str:
        await session.execute(text("SELECT 1"))
        return "ok"

    add_ready_check("db", check_db)

The registered checks run concurrently; if any raises, /ready returns 503.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from shared_py.web.schemas import HealthResponse, ReadyResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Registry: name → async callable returning "ok" or raising on failure
_ready_checks: dict[str, Callable[[], Awaitable[str]]] = {}

# Set by create_app() so health responses know which service they belong to
_service_name: str = "service"


def set_service_name(name: str) -> None:
    global _service_name  # noqa: PLW0603
    _service_name = name


def add_ready_check(name: str, fn: Callable[[], Awaitable[str]]) -> None:
    """
    Register an async readiness check.

    Args:
        name: identifier shown in the /ready response (e.g. "db", "redis")
        fn:   async callable that returns "ok" or raises an exception on failure
    """
    _ready_checks[name] = fn


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health() -> HealthResponse:
    """Liveness probe — returns 200 if the process is running."""
    return HealthResponse(status="ok", service=_service_name)


@router.get("/ready", response_model=ReadyResponse, status_code=200)
async def ready() -> Any:
    """
    Readiness probe — runs all registered dependency checks concurrently.
    Returns 200 when all pass, 503 when any fail.
    """
    if not _ready_checks:
        return ReadyResponse(status="ready", service=_service_name)

    results: dict[str, str] = {}
    failed = False

    async def _run(name: str, fn: Callable[[], Awaitable[str]]) -> tuple[str, str]:
        try:
            result = await fn()
            return name, result
        except Exception as exc:  # noqa: BLE001
            logger.warning("Readiness check '%s' failed: %s", name, exc)
            return name, f"error: {exc}"

    outcomes = await asyncio.gather(
        *[_run(name, fn) for name, fn in _ready_checks.items()]
    )

    for name, result in outcomes:
        results[name] = result
        if result.startswith("error"):
            failed = True

    payload = ReadyResponse(
        status="ready" if not failed else "degraded",
        service=_service_name,
        checks=results,
    )

    if failed:
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
