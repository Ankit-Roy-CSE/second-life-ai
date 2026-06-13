"""
REST routes for the Lifecycle Decision Service.

Endpoints:
    GET /decisions/{return_id}   — fetch lifecycle decision for a return
    GET /decisions               — list all decisions (paginated, for debug)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.models import LifecycleDecision
from app.domain.schemas import DecisionListResponse, DecisionResponse
from app.domain.service import LifecycleService

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("/{return_id}", response_model=DecisionResponse)
async def get_decision(
    return_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the lifecycle decision for a specific return.

    Called by: Passport Service (to build the digital passport),
               API Gateway (for the return detail view).
    """
    service = LifecycleService(db)
    decision = await service.get_decision_by_return_id(return_id)

    if decision is None:
        raise HTTPException(
            status_code=404,
            detail=f"Decision not found for return_id={return_id}",
        )

    return decision


@router.get("", response_model=DecisionListResponse)
async def list_decisions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List all lifecycle decisions (paginated). Primarily for debugging and admin views.
    """
    total_result = await db.execute(select(func.count(LifecycleDecision.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(LifecycleDecision)
        .order_by(LifecycleDecision.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = result.scalars().all()

    return DecisionListResponse(items=list(items), total=total)
