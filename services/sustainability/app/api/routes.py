"""
REST routes for the Sustainability Service.

Endpoints (per SERVICE_ENDPOINTS.md):
    GET /sustainability?return_id=&user_id=    — list records
    GET /sustainability/{id}                   — single record
    GET /sustainability/metrics?user_id=       — aggregated dashboard totals
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.schemas import (
    SustainabilityListResponse,
    SustainabilityMetricsResponse,
    SustainabilityRecordResponse,
)
from app.domain.service import SustainabilityService

router = APIRouter(prefix="/sustainability", tags=["sustainability"])


@router.get("/metrics", response_model=SustainabilityMetricsResponse)
async def get_metrics(
    user_id: Optional[str] = Query(default=None, description="Filter metrics by user_id"),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregated sustainability dashboard totals.

    Called by: API Gateway (dashboard read-model for the Sustainability Dashboard).
    """
    service = SustainabilityService(db)
    return await service.get_metrics(user_id=user_id)


@router.get("/{record_id}", response_model=SustainabilityRecordResponse)
async def get_record(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single sustainability record by its ID."""
    service = SustainabilityService(db)
    record = await service.get_record_by_id(record_id)
    if record is None:
        raise HTTPException(
            status_code=404, detail=f"Record not found: {record_id}"
        )
    return record


@router.get("", response_model=SustainabilityListResponse)
async def list_records(
    return_id: Optional[str] = Query(default=None, description="Filter by return_id"),
    user_id: Optional[str] = Query(default=None, description="Filter by user_id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List sustainability records with optional filters.

    Called by: API Gateway (for per-user sustainability history).
    """
    service = SustainabilityService(db)
    items, total = await service.list_records(
        return_id=return_id, user_id=user_id, limit=limit, offset=offset
    )
    return SustainabilityListResponse(items=items, total=total)
