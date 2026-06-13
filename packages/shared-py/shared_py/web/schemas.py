"""
Shared Pydantic schemas used across all services.

- ErrorDetail / ErrorEnvelope  — the standard error response body
- HealthResponse / ReadyResponse — health and readiness check responses
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Inner object of every error response."""

    code: str = Field(..., description="Machine-readable error code, e.g. 'not_found'")
    message: str = Field(..., description="Human-readable error description")
    correlation_id: str | None = Field(
        None, description="Return/saga ID for cross-service tracing"
    )


class ErrorEnvelope(BaseModel):
    """
    Standard error response body returned by all services.

    Example:
        {
            "error": {
                "code": "not_found",
                "message": "Return abc123 not found",
                "correlation_id": "abc123"
            }
        }
    """

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Liveness probe response — service process is running."""

    status: str = "ok"
    service: str


class ReadyResponse(BaseModel):
    """
    Readiness probe response — service can serve traffic
    (DB and Redis are reachable).
    """

    status: str = "ready"
    service: str
    checks: dict[str, str] = Field(
        default_factory=dict,
        description="Per-dependency check results, e.g. {'db': 'ok', 'redis': 'ok'}",
    )
