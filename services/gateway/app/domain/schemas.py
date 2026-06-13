"""
Pydantic schemas (DTOs) for Gateway Service.

Gateway-specific request/response models. Cross-service contracts are in
packages/shared-py/shared_py/schemas/rest_contracts.py
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════════════
# Returns DTOs
# ═══════════════════════════════════════════════════════════════════════════


class ReturnCreateRequest(BaseModel):
    """
    Request body for POST /returns.
    
    Creates a new return, uploads media to MinIO, emits ReturnSubmitted event.
    """

    product_id: str = Field(..., description="UUID of the Product being returned")
    reason: str = Field(..., min_length=1, description="Return reason")
    media_urls: list[str] = Field(
        default_factory=list,
        description="List of presigned URLs or S3 keys for media (optional)",
    )


class ReturnResponse(BaseModel):
    """
    Response model for return-related endpoints.
    
    Used by POST /returns, GET /returns, GET /returns/{id}.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(..., alias="return_id", description="UUID of the Return")
    product_id: str = Field(..., description="UUID of the Product")
    user_id: str = Field(..., description="UUID of the User")
    reason: str = Field(..., description="Return reason")
    status: str = Field(..., description="ReturnStatus enum value")
    media: list[str] = Field(
        default_factory=list, description="S3/MinIO object keys for media"
    )
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")


class ReturnListResponse(BaseModel):
    """
    Response for GET /returns (paginated list).
    """

    items: list[ReturnResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total count of returns")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class ReturnDetailResponse(BaseModel):
    """
    Response for GET /returns/{id} — BFF aggregation.
    
    Combines Return + Grade + Decision + Passport + Matches.
    """

    return_data: ReturnResponse = Field(..., description="Return entity")
    grade: Optional[dict] = Field(None, description="Grade data (if available)")
    decision: Optional[dict] = Field(None, description="Lifecycle decision (if available)")
    passport: Optional[dict] = Field(None, description="Passport data (if available)")
    matches: list[dict] = Field(default_factory=list, description="Matches (if available)")


# ═══════════════════════════════════════════════════════════════════════════
# Auth proxy DTOs (mirror User Service)
# ═══════════════════════════════════════════════════════════════════════════


class ProxyRegisterRequest(BaseModel):
    """Request body for POST /auth/register (proxied to User Service)."""

    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    display_name: str = Field(..., min_length=1, description="User's display name")
    location: Optional[dict] = Field(
        None, description="Location {lat, lng, city}"
    )
    interests: list[str] = Field(
        default_factory=list, description="Product categories of interest"
    )


class ProxyLoginRequest(BaseModel):
    """Request body for POST /auth/login (proxied to User Service)."""

    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
