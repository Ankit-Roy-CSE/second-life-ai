"""
REST routes for the AI Grading Service.

Endpoints:
    GET /grades/{return_id}   — fetch grade result for a return
    GET /grades               — list all grades (paginated, for debug)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.models import Grade
from app.domain.schemas import GradeListResponse, GradeResponse
from app.domain.service import GradingService

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("/{return_id}", response_model=GradeResponse)
async def get_grade(
    return_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the AI grading result for a specific return.

    Called by: Lifecycle Decision Service (to decide next action),
               API Gateway (for the return detail view).
    """
    service = GradingService(db)
    grade = await service.get_grade_by_return_id(return_id)

    if grade is None:
        raise HTTPException(
            status_code=404,
            detail=f"Grade not found for return_id={return_id}",
        )

    return grade


@router.get("", response_model=GradeListResponse)
async def list_grades(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List all grades (paginated). Primarily for debugging and admin views.
    """
    total_result = await db.execute(select(func.count(Grade.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Grade).order_by(Grade.created_at.desc()).limit(limit).offset(offset)
    )
    items = result.scalars().all()

    return GradeListResponse(items=list(items), total=total)
