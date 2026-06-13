"""
Shared ASGI middleware for all Amazon Second Life AI services.

CorrelationIdMiddleware
    - Reads X-Correlation-Id from incoming requests
    - Generates a new UUID if absent
    - Propagates it to the response header
    - Makes it available on request.state.correlation_id

RequestLoggingMiddleware
    - Logs every request/response as a single structured JSON line
    - Skips /health and /ready to avoid log noise
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_SKIP_PATHS = frozenset({"/health", "/ready"})


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request carries a correlation_id."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP request/response pairs as structured JSON."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        correlation_id = getattr(request.state, "correlation_id", None)

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
            },
        )
        return response
