"""
FastAPI routes for User Service.

Thin layer: validate input, call service, return response.
No business logic here — that lives in domain/service.py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.schemas import (
    GreenCreditsResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserCandidatesListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.domain.service import UserService

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════
# Auth endpoints
# ═════════════════════════════════════════════════════════════════════════


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register a new user",
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.
    
    - Validates email uniqueness.
    - Hashes password with bcrypt.
    - Returns user profile (no password_hash).
    
    Called by: Frontend via Gateway.
    """
    service = UserService(db)
    return await service.register(request)


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["auth"],
    summary="Login and get JWT",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user and issue JWT access token.
    
    - Verifies email and password.
    - Issues JWT with user ID as subject.
    - Returns token + user profile.
    
    Called by: Frontend via Gateway.
    """
    service = UserService(db)
    return await service.login(request)


# ═════════════════════════════════════════════════════════════════════════
# User profile endpoints
# ═════════════════════════════════════════════════════════════════════════


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Get user profile",
)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Get user profile by ID.
    
    Called by: Frontend via Gateway, or other services.
    """
    service = UserService(db)
    return await service.get_user(user_id)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Update user profile",
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update user profile fields (display_name, location, interests).
    
    All fields are optional.
    
    Called by: Frontend via Gateway.
    """
    service = UserService(db)
    return await service.update_user(user_id, request)


@router.get(
    "/users/{user_id}/credits",
    response_model=GreenCreditsResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Get green credit balance",
)
async def get_credits(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> GreenCreditsResponse:
    """
    Get user's green credit balance.
    
    Called by: Frontend via Gateway.
    """
    service = UserService(db)
    return await service.get_credits(user_id)


# ═════════════════════════════════════════════════════════════════════════
# Cross-service endpoint (for Matching)
# ═════════════════════════════════════════════════════════════════════════


@router.get(
    "/users/candidates",
    response_model=UserCandidatesListResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Find candidate buyers (cross-service)",
)
async def find_candidates(
    category: Optional[str] = Query(None, description="Product category filter"),
    lat: Optional[float] = Query(None, description="Product latitude"),
    lng: Optional[float] = Query(None, description="Product longitude"),
    radius_km: Optional[float] = Query(None, description="Search radius in km"),
    db: AsyncSession = Depends(get_db),
) -> UserCandidatesListResponse:
    """
    Find candidate buyers for hyperlocal matching.
    
    Filters:
    - category: Users with this category in their interests.
    - lat/lng/radius_km: Users within radius (Haversine distance).
    
    Called by: Matching service (server-to-server).
    """
    service = UserService(db)
    return await service.find_candidates(
        category=category,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )
