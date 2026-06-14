"""
REST routes for the Hyperlocal Matching Service.

Endpoints:
    GET /matches?return_id=          — list matches for a return
    GET /matches/{id}                — fetch a single match by ID
    GET /listings?channel=&status=&category=&limit=&offset=
                                     — list listings with optional filters
    GET /listings/{id}               — fetch a single listing by ID
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.domain.schemas import (
    ListingListResponse,
    ListingResponse,
    MatchListResponse,
    MatchResponse,
)
from app.domain.service import MatchingService

router = APIRouter(tags=["matching"])


def _make_service(db: AsyncSession) -> MatchingService:
    return MatchingService(
        db=db,
        user_service_url=settings.user_service_url,
        radius_km=settings.match_radius_km,
        score_threshold=settings.match_score_threshold,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Match endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/matches", response_model=MatchListResponse)
async def list_matches(
    return_id: str = Query(..., description="Filter matches by return_id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List all matches for a given return, sorted by score descending.

    Called by: API Gateway (for the return detail / match results view).
    """
    service = _make_service(db)
    items, total = await service.get_matches_for_return(
        return_id=return_id, limit=limit, offset=offset
    )
    return MatchListResponse(items=items, total=total)


@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single match record by its ID."""
    service = _make_service(db)
    match = await service.get_match_by_id(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match not found: {match_id}")
    return match


# ─────────────────────────────────────────────────────────────────────────────
# Listing endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/listings", response_model=ListingListResponse)
async def list_listings(
    channel: Optional[str] = Query(
        default=None, description="Filter by channel (HYPERLOCAL|MARKETPLACE)"
    ),
    status: Optional[str] = Query(
        default=None, description="Filter by status (ACTIVE|RESERVED|SOLD|EXPIRED)"
    ),
    category: Optional[str] = Query(
        default=None, description="Filter by product category (best-effort)"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List product listings with optional filters.

    Called by: API Gateway (marketplace / matches UI views).
    """
    service = _make_service(db)
    items, total = await service.list_listings(
        channel=channel,
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )
    return ListingListResponse(items=items, total=total)


@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single listing record by its ID."""
    service = _make_service(db)
    listing = await service.get_listing_by_id(listing_id)
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing not found: {listing_id}"
        )
    return listing
