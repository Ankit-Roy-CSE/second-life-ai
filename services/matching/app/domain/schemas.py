"""
Pydantic request/response DTOs for the Hyperlocal Matching Service.

These are service-specific schemas.  Shared types (ListingChannel, ListingStatus)
live in shared_py.schemas.enums.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from shared_py.schemas.enums import ListingChannel, ListingStatus


# ─────────────────────────────────────────────────────────────────────────────
# User Service candidate (returned by GET /users/candidates)
# ─────────────────────────────────────────────────────────────────────────────


class UserCandidate(BaseModel):
    """Single buyer candidate as returned by the User Service."""

    id: str
    display_name: str
    lat: float
    lng: float
    interests: list[str] = Field(default_factory=list)


class UserCandidatesListResponse(BaseModel):
    """Response from GET /users/candidates."""

    items: list[UserCandidate]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# Match responses
# ─────────────────────────────────────────────────────────────────────────────


class MatchResponse(BaseModel):
    """Response for GET /matches/{id} and list items."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    match_request_id: str
    buyer_user_id: str
    score: float = Field(..., ge=0.0, le=100.0)
    estimated_savings: float = Field(..., ge=0.0)
    distance_km: float = Field(..., ge=0.0)
    rationale: str
    created_at: datetime


class MatchListResponse(BaseModel):
    """Response for GET /matches?return_id=."""

    items: list[MatchResponse]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# Listing responses
# ─────────────────────────────────────────────────────────────────────────────


class ListingResponse(BaseModel):
    """Response for GET /listings/{id} and list items."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    passport_id: str
    price: float = Field(..., ge=0.0)
    channel: ListingChannel
    status: ListingStatus
    created_at: datetime


class ListingListResponse(BaseModel):
    """Response for GET /listings (paginated)."""

    items: list[ListingResponse]
    total: int
