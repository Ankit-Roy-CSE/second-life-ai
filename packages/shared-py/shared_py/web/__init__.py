"""shared-py/web — FastAPI app factory, health, error handlers, CORS, logging."""

from shared_py.web.auth import create_access_token, decode_access_token
from shared_py.web.errors import (
    AppError,
    ErrorEnvelope,
    app_error_handler,
    http_exception_handler,
)
from shared_py.web.factory import create_app
from shared_py.web.health import add_ready_check
from shared_py.web.health import router as health_router
from shared_py.web.schemas import ErrorDetail, HealthResponse, ReadyResponse

__all__ = [
    # Factory
    "create_app",
    # Health
    "health_router",
    "add_ready_check",
    # Errors
    "AppError",
    "ErrorEnvelope",
    "ErrorDetail",
    "http_exception_handler",
    "app_error_handler",
    # Responses
    "HealthResponse",
    "ReadyResponse",
    # Auth helpers
    "create_access_token",
    "decode_access_token",
]
