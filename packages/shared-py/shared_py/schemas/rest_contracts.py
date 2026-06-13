"""
REST API contracts for cross-service communication.

These DTOs define the request/response shapes for endpoints that are called
by other services (not just the Gateway). Each service owns its own detailed
schemas in its `domain/schemas.py`, but cross-service contracts live here so
both caller and callee reference the same types.

Cross-service read patterns (from architecture.md):
- Matching → User: GET /users/candidates (find nearby buyers)
- Gateway creates Return entity (owns the Return table)
- Passport owns the canonical Product entity
"""

from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# User Service — Cross-service contracts
# ═══════════════════════════════════════════════════════════════════════════


class UserCandidateResponse(BaseModel):
    """
    Response model for GET /users/candidates.
    
    Called by: Matching Service (to find nearby buyers).
    Owner: User Service (A).
    """

    user_id: str = Field(..., description="UUID of the candidate user")
    display_name: str = Field(..., description="User's display name")
    location: dict[str, float] = Field(
        ..., description="User location {lat, lng, city}"
    )
    interests: list[str] = Field(
        default_factory=list, description="Product categories the user is interested in"
    )
    distance_km: Optional[float] = Field(
        None, description="Distance from the product location (if calculated)"
    )


class UserCandidatesListResponse(BaseModel):
    """
    List response for GET /users/candidates?category=&lat=&lng=&radius_km=
    """

    candidates: list[UserCandidateResponse] = Field(
        default_factory=list, description="List of candidate buyers"
    )
    total: int = Field(..., description="Total count of candidates")


# ═══════════════════════════════════════════════════════════════════════════
# Gateway — Return entity (created by Gateway, read by services)
# ═══════════════════════════════════════════════════════════════════════════


class ReturnCreateRequest(BaseModel):
    """
    Request model for POST /returns (Gateway endpoint).
    
    Owner: Gateway (A).
    """

    product_id: str = Field(..., description="UUID of the Product being returned")
    reason: str = Field(..., description="Return reason (user-provided text)")
    media_urls: list[str] = Field(
        default_factory=list,
        description="Presigned upload URLs or S3 keys for images/videos",
    )


class ReturnResponse(BaseModel):
    """
    Response model for return-related endpoints.
    
    Read by: All services (via Gateway or internal calls).
    Owner: Gateway (A).
    """

    return_id: str = Field(..., alias="id", description="UUID of the Return")
    product_id: str = Field(..., description="UUID of the Product")
    user_id: str = Field(..., description="UUID of the User")
    reason: str = Field(..., description="Return reason")
    status: str = Field(..., description="ReturnStatus enum value")
    media: list[str] = Field(
        default_factory=list, description="S3/MinIO object keys for media"
    )
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")

    class Config:
        populate_by_name = True  # Allow both 'id' and 'return_id'


# ═══════════════════════════════════════════════════════════════════════════
# Passport Service — Product entity (canonical source)
# ═══════════════════════════════════════════════════════════════════════════


class ProductResponse(BaseModel):
    """
    Response model for product-related endpoints.
    
    Owner: Passport Service (A) — owns the canonical Product table.
    Read by: All services (via Gateway or internal calls).
    """

    product_id: str = Field(..., alias="id", description="UUID of the Product")
    owner_user_id: str = Field(..., description="UUID of the current owner")
    category: str = Field(..., description="Product category (e.g. 'Electronics')")
    title: str = Field(..., description="Product title/name")
    brand: Optional[str] = Field(None, description="Product brand")
    attributes: dict = Field(
        default_factory=dict, description="Additional product attributes (JSON)"
    )
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")

    class Config:
        populate_by_name = True


# ═══════════════════════════════════════════════════════════════════════════
# Pagination (standard across all services)
# ═══════════════════════════════════════════════════════════════════════════


class PaginatedResponse(BaseModel):
    """
    Standard pagination envelope for list endpoints.
    
    Usage:
        class MyListResponse(PaginatedResponse):
            items: list[MyModel]
    """

    total: int = Field(..., description="Total count of items (all pages)")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


# ═══════════════════════════════════════════════════════════════════════════
# Health & Error (used by all services via shared-py/web)
# ═══════════════════════════════════════════════════════════════════════════


class HealthResponse(BaseModel):
    """Standard health check response."""

    status: str = Field(default="ok", description="Health status")
    service: str = Field(..., description="Service name")


class ErrorEnvelope(BaseModel):
    """
    Standard error response envelope (already implemented in shared-py/web/schemas.py).
    
    Included here for reference — this is the shape returned by all error handlers.
    """

    error: dict[str, str] = Field(
        ...,
        description="Error object with code, message, and correlation_id fields",
    )
