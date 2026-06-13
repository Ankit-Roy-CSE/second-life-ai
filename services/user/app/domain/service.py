"""
Business logic for User Service.

No FastAPI imports — pure domain logic. Called by routes.
"""

import uuid
from math import asin, cos, radians, sin, sqrt
from typing import Optional

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.web.auth import create_access_token
from shared_py.web.errors import AppError

from app.config import settings
from app.db.repository import UserRepository
from app.domain.models import User
from app.domain.schemas import (
    GreenCreditsResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserCandidateResponse,
    UserCandidatesListResponse,
    UserResponse,
    UserUpdateRequest,
)

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """User service with business logic for auth, profile, credits."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    # ═════════════════════════════════════════════════════════════════════
    # Auth methods
    # ═════════════════════════════════════════════════════════════════════

    async def register(self, request: RegisterRequest) -> UserResponse:
        """
        Register a new user.
        
        1. Check if email already exists.
        2. Hash password with bcrypt.
        3. Create User entity.
        4. Return UserResponse (no password_hash).
        
        Args:
            request: RegisterRequest with email, password, display_name, etc.
        
        Returns:
            UserResponse.
        
        Raises:
            AppError(409) if email already exists.
        """
        # Check if email already exists
        existing = await self.repo.get_by_email(request.email)
        if existing:
            raise AppError(
                status_code=409,
                code="email_exists",
                message=f"Email {request.email} is already registered",
            )

        # Hash password
        password_hash = pwd_context.hash(request.password)

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            password_hash=password_hash,
            display_name=request.display_name,
            location=request.location,
            interests=request.interests,
            green_credits=0.0,
        )

        user = await self.repo.create(user)

        return self._to_user_response(user)

    async def login(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate user and issue JWT.
        
        1. Find user by email.
        2. Verify password with bcrypt.
        3. Issue JWT with user ID as subject.
        4. Return token + user profile.
        
        Args:
            request: LoginRequest with email and password.
        
        Returns:
            LoginResponse with access_token and user profile.
        
        Raises:
            AppError(401) if credentials are invalid.
        """
        user = await self.repo.get_by_email(request.email)
        if not user:
            raise AppError(
                status_code=401,
                code="invalid_credentials",
                message="Invalid email or password",
            )

        # Verify password
        if not pwd_context.verify(request.password, user.password_hash):
            raise AppError(
                status_code=401,
                code="invalid_credentials",
                message="Invalid email or password",
            )

        # Issue JWT
        access_token = create_access_token(
            subject=str(user.id),
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            expire_minutes=settings.jwt_expire_minutes,
        )

        return LoginResponse(
            access_token=access_token,
            user=self._to_user_response(user),
        )

    # ═════════════════════════════════════════════════════════════════════
    # Profile methods
    # ═════════════════════════════════════════════════════════════════════

    async def get_user(self, user_id: str) -> UserResponse:
        """
        Get user profile by ID.
        
        Args:
            user_id: UUID string.
        
        Returns:
            UserResponse.
        
        Raises:
            AppError(404) if user not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AppError(
                status_code=404,
                code="user_not_found",
                message=f"User {user_id} not found",
            )
        return self._to_user_response(user)

    async def update_user(
        self, user_id: str, request: UserUpdateRequest
    ) -> UserResponse:
        """
        Update user profile.
        
        Args:
            user_id: UUID string.
            request: UserUpdateRequest with optional fields.
        
        Returns:
            Updated UserResponse.
        
        Raises:
            AppError(404) if user not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AppError(
                status_code=404,
                code="user_not_found",
                message=f"User {user_id} not found",
            )

        # Update fields if provided
        if request.display_name is not None:
            user.display_name = request.display_name
        if request.location is not None:
            user.location = request.location
        if request.interests is not None:
            user.interests = request.interests

        user = await self.repo.update(user)
        return self._to_user_response(user)

    async def get_credits(self, user_id: str) -> GreenCreditsResponse:
        """
        Get green credit balance.
        
        Args:
            user_id: UUID string.
        
        Returns:
            GreenCreditsResponse with balance.
        
        Raises:
            AppError(404) if user not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AppError(
                status_code=404,
                code="user_not_found",
                message=f"User {user_id} not found",
            )
        return GreenCreditsResponse(green_credits=user.green_credits)

    # ═════════════════════════════════════════════════════════════════════
    # Cross-service: Find buyer candidates (for Matching)
    # ═════════════════════════════════════════════════════════════════════

    async def find_candidates(
        self,
        category: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_km: Optional[float] = None,
    ) -> UserCandidatesListResponse:
        """
        Find candidate buyers for hyperlocal matching.
        
        Called by: Matching service via GET /users/candidates.
        
        Filters:
        - category: Users with this category in their interests.
        - lat/lng/radius_km: Users within radius (Haversine distance).
        
        Args:
            category: Product category (e.g., "Electronics").
            lat: Product latitude.
            lng: Product longitude.
            radius_km: Search radius in kilometers.
        
        Returns:
            UserCandidatesListResponse with matched candidates.
        """
        # Fetch candidates from repository (simplified query)
        users = await self.repo.find_candidates(
            category=category,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            limit=50,
        )

        candidates = []
        for user in users:
            # Filter by category if provided
            if category and category not in user.interests:
                continue

            # Calculate distance if location params provided
            distance_km = None
            if lat is not None and lng is not None and user.location:
                user_lat = user.location.get("lat")
                user_lng = user.location.get("lng")
                if user_lat is not None and user_lng is not None:
                    distance_km = self._haversine_distance(
                        lat, lng, user_lat, user_lng
                    )

                    # Filter by radius if provided
                    if radius_km is not None and distance_km > radius_km:
                        continue

            candidates.append(
                UserCandidateResponse(
                    user_id=user.id,
                    display_name=user.display_name,
                    location=user.location or {},
                    interests=user.interests,
                    distance_km=distance_km,
                )
            )

        # Sort by distance if calculated
        if lat is not None and lng is not None:
            candidates.sort(
                key=lambda c: c.distance_km if c.distance_km is not None else float("inf")
            )

        return UserCandidatesListResponse(
            candidates=candidates,
            total=len(candidates),
        )

    # ═════════════════════════════════════════════════════════════════════
    # Helper methods
    # ═════════════════════════════════════════════════════════════════════

    def _to_user_response(self, user: User) -> UserResponse:
        """
        Convert User ORM model to UserResponse DTO.
        
        Never include password_hash in response.
        """
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            location=user.location,
            interests=user.interests,
            green_credits=user.green_credits,
            created_at=user.created_at.isoformat(),
        )

    @staticmethod
    def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two lat/lng points using Haversine formula.
        
        Args:
            lat1, lng1: First point coordinates.
            lat2, lng2: Second point coordinates.
        
        Returns:
            Distance in kilometers.
        """
        # Radius of Earth in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = radians(lat1)
        lng1_rad = radians(lng1)
        lat2_rad = radians(lat2)
        lng2_rad = radians(lng2)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        # Haversine formula
        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2) ** 2
        c = 2 * asin(sqrt(a))

        return R * c
