"""
FastAPI routes for Gateway Service.

Gateway is the single entry point for the frontend:
- Proxies auth endpoints to User Service
- Creates Return entities and emits ReturnSubmitted events
- Aggregates data from multiple services (BFF pattern)
- Proxies Passport and Matches routes
- Handles purchase trigger (PurchaseCompleted event)
- Proxies marketplace listings
"""

import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.events.client import publish
from shared_py.schemas.enums import ReturnStatus
from shared_py.web.errors import AppError

from app.api.middleware import get_current_user_id, require_auth
from app.clients.http_client import service_client
from app.config import settings
from app.db.session import get_db
from app.domain.models import Return
from app.domain.schemas import (
    ProxyLoginRequest,
    ProxyRegisterRequest,
    PurchaseRequest,
    PurchaseResponse,
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
    3. Emit ReturnSubmitted event to start the saga
    4. Return ReturnResponse
    """
    # Require authentication
    user_id = require_auth(user_id)

    # Create Return entity
    return_entity = Return(
        id=str(uuid.uuid4()),
        product_id=request.product_id,
        user_id=user_id,
        reason=request.reason,
        media=request.media_urls,
        status=ReturnStatus.SUBMITTED.value,
    )

    db.add(return_entity)
    await db.flush()
    await db.refresh(return_entity)

    # Emit ReturnSubmitted event (critical for saga)
    try:
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
            redis_url=settings.redis_url,
            producer="gateway",
        )
    except Exception as e:
        # If event publish fails, rollback the transaction
        await db.rollback()
        raise HTTPException(
            status_code=503,
            detail=f"Failed to publish ReturnSubmitted event: {e}",
        ) from e

    # Commit transaction only after successful event publish
    await db.commit()

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
    """
    from sqlalchemy import func

    query = select(Return)
    count_query = select(func.count()).select_from(Return)

    if user_id_filter:
        query = query.where(Return.user_id == user_id_filter)
        count_query = count_query.where(Return.user_id == user_id_filter)
    if status_filter:
        query = query.where(Return.status == status_filter)
        count_query = count_query.where(Return.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.limit(limit).offset(offset).order_by(Return.created_at.desc())
    result = await db.execute(query)
    returns = result.scalars().all()

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

    Upstream 404/unreachable → field set to null/[] (partial availability).
    """
    # 1. Require authentication
    user_id = require_auth(user_id)

    # 2. DB lookup
    result = await db.execute(select(Return).where(Return.id == return_id))
    return_entity = result.scalar_one_or_none()

    if not return_entity:
        raise AppError(
            status_code=404,
            code="not_found",
            message=f"Return {return_id} not found",
            correlation_id=return_id,
        )

    # 3. Concurrent fan-out to all four upstream services
    grade_result, decision_result, passport_result, matches_result = await asyncio.gather(
        service_client.get_grade(return_id, user_id),
        service_client.get_decision(return_id, user_id),
        service_client.get_passport_by_return(return_id, user_id),
        service_client.get_matches(return_id, user_id),
    )

    # 4. Build the aggregated response
    return_response = ReturnResponse(
        id=return_entity.id,
        product_id=return_entity.product_id,
        user_id=return_entity.user_id,
        reason=return_entity.reason,
        status=return_entity.status,
        media=return_entity.media,
        created_at=return_entity.created_at.isoformat(),
    )

    return ReturnDetailResponse(
        return_data=return_response,
        grade=grade_result,
        decision=decision_result,
        passport=passport_result,
        matches=matches_result if matches_result is not None else [],
    )


# ═════════════════════════════════════════════════════════════════════════
# Passport proxy route
# ═════════════════════════════════════════════════════════════════════════


@router.get(
    "/passports/{passport_id}",
    status_code=status.HTTP_200_OK,
    tags=["passports"],
    summary="Get passport by ID (proxy to Passport Service)",
)
async def get_passport(
    passport_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Proxy GET /passports/{passport_id} to Passport Service.

    - 404 from upstream → re-raises AppError(404)
    - ConnectError → AppError(502, "upstream_unreachable")
    """
    user_id = require_auth(user_id)
    body = await service_client.get_passport(passport_id, user_id)
    return JSONResponse(content=body)


# ═════════════════════════════════════════════════════════════════════════
# Matches proxy route
# ═════════════════════════════════════════════════════════════════════════


@router.get(
    "/matches",
    status_code=status.HTTP_200_OK,
    tags=["matches"],
    summary="Get matches for a return (proxy to Matching Service)",
)
async def get_matches(
    return_id: str = Query(..., description="UUID of the Return"),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Proxy GET /matches?return_id= to Matching Service.

    - return_id is required (FastAPI returns 422 if absent)
    - 404 from upstream → re-raises AppError(404)
    - ConnectError → AppError(502, "upstream_unreachable")
    """
    user_id = require_auth(user_id)
    body = await service_client.get_matches_for_return(return_id, user_id)
    return JSONResponse(content=body)


# ═════════════════════════════════════════════════════════════════════════
# Purchase trigger (PurchaseCompleted event)
# ═════════════════════════════════════════════════════════════════════════


@router.post(
    "/purchase",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["purchase"],
    summary="Trigger a purchase and emit PurchaseCompleted event",
)
async def post_purchase(
    request: PurchaseRequest,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Trigger a purchase.

    Steps:
    1. Require authentication
    2. Validate buyer_user_id == JWT user_id
    3. Lookup listing → get return_id (correlation_id)
    4. Publish PurchaseCompleted event
    5. Return HTTP 201 with PurchaseResponse

    buyer_user_id in the event is ALWAYS the JWT-derived user_id.
    """
    # 1. Require authentication
    user_id = require_auth(user_id)

    # 2. Validate buyer_user_id matches JWT user
    if request.buyer_user_id != user_id:
        raise AppError(
            status_code=403,
            code="forbidden",
            message="buyer_user_id must match the authenticated user",
        )

    # 3. Lookup listing to get return_id
    listing = await service_client.get_listing(request.listing_id, user_id)
    correlation_id = listing["return_id"]

    # 4. Publish PurchaseCompleted event
    try:
        event_id = await publish(
            event_type="PurchaseCompleted",
            correlation_id=correlation_id,
            data={
                "listing_id": request.listing_id,
                "product_id": listing.get("product_id", ""),
                "return_id": correlation_id,
                "buyer_user_id": user_id,  # MUST come from JWT, not request body
                "price": request.price,
            },
            redis_url=settings.redis_url,
            producer="gateway",
        )
    except Exception as e:
        raise AppError(
            status_code=503,
            code="event_publish_failed",
            message=f"Failed to publish PurchaseCompleted event: {e}",
            correlation_id=correlation_id,
        ) from e

    # 5. Return 201
    return PurchaseResponse(
        listing_id=request.listing_id,
        buyer_user_id=user_id,
        price=request.price,
        event_id=event_id,
        correlation_id=correlation_id,
    )


# ═════════════════════════════════════════════════════════════════════════
# Marketplace proxy route
# ═════════════════════════════════════════════════════════════════════════


@router.get(
    "/marketplace",
    status_code=status.HTTP_200_OK,
    tags=["marketplace"],
    summary="Browse marketplace listings (proxy to Matching Service with retry)",
)
async def get_marketplace(
    category: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Proxy GET /marketplace to Matching Service listings endpoint.

    Always appends channel=MARKETPLACE and status=ACTIVE.
    Defaults: limit=20, offset=0.
    Retries up to 3 times with back-off on ConnectError.
    """
    user_id = require_auth(user_id)

    # Apply defaults
    effective_limit = limit if limit is not None else 20
    effective_offset = offset if offset is not None else 0

    # Build params dict — always include fixed filters
    params: dict = {
        "channel": "MARKETPLACE",
        "status": "ACTIVE",
        "limit": effective_limit,
        "offset": effective_offset,
    }
    if category is not None:
        params["category"] = category

    body = await service_client._marketplace_with_retry(params, user_id)
    return JSONResponse(content=body)
