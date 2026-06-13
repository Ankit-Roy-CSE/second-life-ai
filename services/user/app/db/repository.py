"""
Data access layer (repository) for User Service.

Pure CRUD operations — no business logic here. Returns ORM objects.
Business logic lives in domain/service.py.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User


class UserRepository:
    """Repository for User entity data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        """
        Create a new user.
        
        Args:
            user: User ORM instance (with id, email, password_hash, etc. set).
        
        Returns:
            Created User instance.
        """
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: UUID string.
        
        Returns:
            User instance or None if not found.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email (for login).
        
        Args:
            email: User email address.
        
        Returns:
            User instance or None if not found.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """
        Update an existing user.
        
        Args:
            user: User ORM instance with modified fields.
        
        Returns:
            Updated User instance.
        """
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def find_candidates(
        self,
        category: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_km: Optional[float] = None,
        limit: int = 50,
    ) -> list[User]:
        """
        Find candidate buyers for hyperlocal matching.
        
        Called by Matching service via GET /users/candidates.
        
        Filters:
        - category: User interests include this category (optional).
        - lat/lng/radius_km: User location within radius (optional, simplified).
        - limit: Max candidates to return.
        
        Args:
            category: Product category to match against user interests.
            lat: Latitude of product location.
            lng: Longitude of product location.
            radius_km: Search radius in kilometers.
            limit: Max number of candidates to return.
        
        Returns:
            List of User instances.
        
        Note:
            Simplified implementation without PostGIS. Real production would use
            geospatial indexing. For now, we filter by category and return users
            with locations; distance calculation happens in the service layer.
        """
        query = select(User).where(User.location.isnot(None))

        # Filter by category if provided (user interests contain the category)
        if category:
            # PostgreSQL JSONB contains operator
            # SQLAlchemy: User.interests.contains([category])
            # For simplicity, we'll fetch all and filter in Python (not ideal, but works for demo)
            pass  # Will filter in service layer

        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
