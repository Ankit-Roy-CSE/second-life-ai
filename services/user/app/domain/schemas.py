"""
Pydantic schemas (DTOs) for User Service request/response models.

These are User Service-specific. Cross-service contracts live in
packages/shared-py/shared_py/schemas/rest_contracts.py
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════════════
# Auth DTOs
# ═══════════════════════════════════════════════════════════════════════════


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    email: EmailStr = Field(..., description="User email (unique)")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    display_name: str = Field(..., min_length=1, description="User's display name")
    location: Optional[dict] = Field(
        None, description="Location {lat, lng, city} for hyperlocal matching"
    )
    interests: list[str] = Field(
        default_factory=list, description="Product categories of interest"
    )


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Response for POST /auth/login."""

    access_token: str = Field(..., description="JWT access token")
    user: "UserResponse" = Field(..., description="User profile data")


# ═══════════════════════════════════════════════════════════════════════════
# User DTOs
# ═══════════════════════════════════════════════════════════════════════════


class UserResponse(BaseModel):
    """User profile response (never includes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID of the user")
    email: str = Field(..., description="User email")
    display_name: str = Field(..., description="User's display name")
    location: Optional[dict] = Field(
        None, description="Location {lat, lng, city}"
    )
    interests: list[str] = Field(
        default_factory=list, description="Product categories of interest"
    )
    green_credits: float = Field(..., description="Accumulated green credits")
    created_at: str = Field(..., description="ISO-8601 UTC timestamp")


class UserUpdateRequest(BaseModel):
    """Request body for PATCH /users/{id} — all fields optional."""

    display_name: Optional[str] = Field(None, min_length=1)
    location: Optional[dict] = Field(None)
    interests: Optional[list[str]] = Field(None)


class GreenCreditsResponse(BaseModel):
    """Response for GET /users/{id}/credits."""

    green_credits: float = Field(..., description="Current green credit balance")


# ═══════════════════════════════════════════════════════════════════════════
# Buyer Candidates (cross-service contract for Matching)
# ═══════════════════════════════════════════════════════════════════════════


class UserCandidateResponse(BaseModel):
    """
    Single candidate buyer (for Matching service).
    Mirrors shared_py.schemas.rest_contracts.UserCandidateResponse
    """

    user_id: str = Field(..., description="UUID of the candidate user")
    display_name: str = Field(..., description="User's display name")
    location: dict = Field(..., description="User location {lat, lng, city}")
    interests: list[str] = Field(
        default_factory=list, description="Product categories of interest"
    )
    distance_km: Optional[float] = Field(
        None, description="Distance from product location (calculated by caller)"
    )


class UserCandidatesListResponse(BaseModel):
    """
    Response for GET /users/candidates (cross-service call from Matching).
    Mirrors shared_py.schemas.rest_contracts.UserCandidatesListResponse
    """

    candidates: list[UserCandidateResponse] = Field(
        default_factory=list, description="List of candidate buyers"
    )
    total: int = Field(..., description="Total count of candidates")
