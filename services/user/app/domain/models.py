"""
SQLAlchemy ORM models for User Service.

Domain Model (from architecture.md §5):
- User: id, email, password_hash, display_name, location (lat/lng/city),
  interests[], green_credits, created_at
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all User Service models."""

    pass


class User(Base):
    """
    User entity — owns authentication, profile, preferences, and green credits.

    Key fields:
    - id: UUID v4 string (PK)
    - email: unique, for login
    - password_hash: bcrypt hash (never log or return this)
    - display_name: user's display name
    - location: JSON {lat, lng, city} for hyperlocal matching
    - interests: JSON array of product categories the user is interested in
    - green_credits: float, accumulated sustainability credits
    - created_at: UTC timestamp
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)

    # Location for hyperlocal matching (JSON: {lat, lng, city})
    location: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Product categories user is interested in (JSON array)
    interests: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Green credits accumulated through sustainable actions
    green_credits: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, display_name={self.display_name})>"
