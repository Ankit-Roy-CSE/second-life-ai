"""
FastAPI routes for Gateway Service.

Gateway is the single entry point for the frontend:
- Proxies auth endpoints to User Service
- Creates Return entities and emits ReturnSubmitted events
- Aggregates data from multiple services (BFF pattern)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.events.client import publish
from shared_py.schemas.enums import ReturnStatus

from app.api.middleware import get_current_user_id, require_auth
from app.clients.http_client import service_client
from app.db.session import get_db
from app.domain.models import Return
from app.domain.schemas import (
    ProxyLoginRequest,
    ProxyRegisterRequest,
    ReturnCreateRequest,
    ReturnDetailResponse,
    ReturnListResponse,
    ReturnResponse,
)

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════
# Auth endpoints (proxy to User Service)
# ═════════════════════════════════════════════════════════════════════════


@router.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register a new user (proxy to User Service)",
)
async def register(request: ProxyRegisterRequest):
    """
    Proxy registration to User Service.
    
    User Service handles password hashing and user creation.
    Returns user profile (no JWT from this endpoint).
    """
    return await service_client.proxy_to_user_service(
        "POST",
        "/auth/register",
        json=request.model_dump(),
    )


@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    tags=["auth"],
    summary="Login and get JWT (proxy to User Service)",
)
async def login(request: ProxyLoginRequest):
    """
    Proxy login to User Service.
    
    User Service verifies credentials and issues JWT.
    Returns { access_token, user }.
    """
    return await service_client.proxy_to_user_service(
        "POST",
        "/auth/login",
        json=request.model_dump(),
    )


# ═════════════════════════════════════════════════════════════════════════
# Returns endpoints (Gateway owns Return table)
# ═════════════════════════════════════════════════════════════════════════


@router.post(
    "/returns",
    response_model=ReturnResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["returns"],
    summary="Create a new return",
)
async def create_return(
    request: ReturnCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Create a new product return.
    
    Steps:
    1. Verify JWT (user must be authenticated)
    2. Create Return entity in Gateway database
    3. Upload media to MinIO (if provided)
    4. Emit ReturnSubmitted event to start the saga
    5. Return ReturnResponse
    
    Called by: Frontend (after user fills return form)
    """
    # Require authentication
    user_id = require_auth(user_id)

    # Create Return entity
    return_entity = Return(
        id=str(uuid.uuid4()),
        product_id=request.product_id,
        user_id=user_id,
        reason=request.reason,
        media=request.media_urls,  # For demo, assume media_urls are already S3 keys
        status=ReturnStatus.SUBMITTED.value,
    )

    db.add(return_entity)
    await db.flush()
    await db.refresh(return_entity)

    # Emit ReturnSubmitted event
    await publish(
        event_type="ReturnSubmitted",
        correlation_id=return_entity.id,
        data={
            "return_id": return_entity.id,
            "product_id": return_entity.product_id,
            "user_id": return_entity.user_id,
            "reason": return_entity.reason,
            "media": return_entity.media,
        },
    )

    # Return response
    return ReturnResponse(
        id=return_entity.id,
        product_id=return_entity.product_id,
        user_id=return_entity.user_id,
        reason=return_entity.reason,
        status=return_entity.status,
        media=return_entity.media,
        created_at=return_entity.created_at.isoformat(),
    )


@router.get(
    "/returns",
    response_model=ReturnListResponse,
    status_code=status.HTTP_200_OK,
    tags=["returns"],
    summary="List returns (paginated)",
)
async def list_returns(
    user_id_filter: Optional[str] = Query(None, alias="user_id"),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    List returns with optional filtering.
    
    Query params:
    - user_id: Filter by user (optional)
    - status: Filter by ReturnStatus (optional)
    - limit: Items per page (default 20, max 100)
    - offset: Offset from start (default 0)
    
    Returns:
    - Paginated list of returns
    
    Called by: Frontend (returns list view)
    """
    # Build query
    query = select(Return)

    # Apply filters
    if user_id_filter:
        query = query.where(Return.user_id == user_id_filter)
    if status_filter:
        query = query.where(Return.status == status_filter)

    # Get total count
    count_query = select(Return)
    if user_id_filter:
        count_query = count_query.where(Return.user_id == user_id_filter)
    if status_filter:
        count_query = count_query.where(Return.status == status_filter)
    
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    # Apply pagination
    query = query.limit(limit).offset(offset).order_by(Return.created_at.desc())

    # Execute query
    result = await db.execute(query)
    returns = result.scalars().all()

    # Convert to responses
    items = [
        ReturnResponse(
            id=r.id,
            product_id=r.product_id,
            user_id=r.user_id,
            reason=r.reason,
            status=r.status,
            media=r.media,
            created_at=r.created_at.isoformat(),
        )
        for r in returns
    ]

    return ReturnListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/returns/{return_id}",
    response_model=ReturnDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["returns"],
    summary="Get return details (BFF aggregation)",
)
async def get_return_detail(
    return_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Get detailed return information (BFF aggregation).
    
    Aggregates data from:
    - Gateway: Return entity
    - Grading: Grade data (if available)
    - Lifecycle: Decision data (if available)
    - Passport: Passport data (if available)
    - Matching: Matches (if available)
    
    Returns:
    - ReturnDetailResponse with all aggregated data
    
    Called by: Frontend (return detail view)
    
    Note: For P1-A2, only Return data is available.
    Other services will be integrated in later phases.
    """
    # Get Return entity
    result = await db.execute(select(Return).where(Return.id == return_id))
    return_entity = result.scalar_one_or_none()

    if not return_entity:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Return {return_id} not found")

    # Build return response
    return_response = ReturnResponse(
        id=return_entity.id,
        product_id=return_entity.product_id,
        user_id=return_entity.user_id,
        reason=return_entity.reason,
        status=return_entity.status,
        media=return_entity.media,
        created_at=return_entity.created_at.isoformat(),
    )

    # TODO: Aggregate data from other services (P2+)
    # For now, only return the Return entity
    return ReturnDetailResponse(
        return_data=return_response,
        grade=None,
        decision=None,
        passport=None,
        matches=[],
    )
