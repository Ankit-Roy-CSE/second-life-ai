"""
Error handling for Amazon Second Life AI services.

All services raise AppError (or FastAPI's HTTPException) and rely on the
shared exception handlers to emit a consistent ErrorEnvelope response:

    {
        "error": {
            "code": "not_found",
            "message": "Return abc123 not found",
            "correlation_id": "abc123"
        }
    }

Usage in a route / service:
    from shared_py.web.errors import AppError

    raise AppError(status_code=404, code="not_found", message="Return not found")
    raise AppError(status_code=404, code="not_found", message="...", correlation_id=return_id)

The handlers are registered automatically by create_app().
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared_py.web.schemas import ErrorDetail, ErrorEnvelope

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application-level error class
# ---------------------------------------------------------------------------

class AppError(Exception):
    """
    Raise this from domain / service layers instead of importing FastAPI.
    The shared handler converts it to an ErrorEnvelope JSON response.

    Args:
        status_code: HTTP status code (400, 401, 403, 404, 409, 502, …)
        code:        Machine-readable snake_case string, e.g. "not_found"
        message:     Human-readable description
        correlation_id: Optional return/saga ID for tracing
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.correlation_id = correlation_id


# ---------------------------------------------------------------------------
# Exception handlers — registered by create_app()
# ---------------------------------------------------------------------------

def _make_envelope(
    code: str, message: str, correlation_id: str | None = None
) -> dict:
    return ErrorEnvelope(
        error=ErrorDetail(code=code, message=message, correlation_id=correlation_id)
    ).model_dump()


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError raised from domain/service layers."""
    logger.warning(
        "Application error: %s — %s",
        exc.code,
        exc.message,
        extra={"correlation_id": exc.correlation_id},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_make_envelope(exc.code, exc.message, exc.correlation_id),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Convert FastAPI/Starlette HTTPException to ErrorEnvelope."""
    code = _status_to_code(exc.status_code)
    message = str(exc.detail) if exc.detail else code.replace("_", " ").capitalize()
    correlation_id: str | None = request.headers.get("x-correlation-id")
    logger.warning(
        "HTTP %s: %s",
        exc.status_code,
        message,
        extra={"correlation_id": correlation_id},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_make_envelope(code, message, correlation_id),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic 422 validation errors to ErrorEnvelope."""
    details = "; ".join(
        f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    message = f"Validation error: {details}"
    correlation_id: str | None = request.headers.get("x-correlation-id")
    logger.info("Validation error: %s", details, extra={"correlation_id": correlation_id})
    return JSONResponse(
        status_code=422,
        content=_make_envelope("validation_error", message, correlation_id),
    )


def _status_to_code(status: int) -> str:
    """Map common HTTP status codes to machine-readable error codes."""
    _MAP = {
        400: "bad_request",
        401: "unauthenticated",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
        502: "upstream_error",
        503: "service_unavailable",
    }
    return _MAP.get(status, f"http_{status}")
