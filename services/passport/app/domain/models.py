"""
SQLAlchemy ORM models for the Product Passport Service.

Owns two tables in `slmai_passport`:
  - products     (canonical Product entity per architecture.md §5)
  - passports    (digital product passport)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    """
    Canonical Product entity — owned by the Passport Service (architecture.md §5).

    Created when the first PassportCreated event is processed for a product_id.
    The Gateway passes product_id (from the Return) so we can look up or create it here.
    """

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="electronics")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Returned Product")
    brand: Mapped[str] = mapped_column(String(100), nullable=False, default="Unknown")
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class Passport(Base):
    """
    Digital Product Passport — tracks the full lifecycle of a returned product.

    One Passport per return saga (keyed on return_id/correlation_id).
    Built by combining ProductGraded + LifecycleDecisionCreated event data.

    Status values: PENDING → GRADED → DECIDED → ACTIVE
    """

    __tablename__ = "passports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # return_id doubles as the saga correlation_id
    return_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, unique=True
    )
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Grading data (populated on ProductGraded)
    current_grade: Mapped[str | None] = mapped_column(String(1), nullable=True)
    grade_confidence: Mapped[float | None] = mapped_column(nullable=True)
    damage_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle decision data (populated on LifecycleDecisionCreated)
    lifecycle_action: Mapped[str | None] = mapped_column(String(20), nullable=True)
    value_recovery_estimate: Mapped[float | None] = mapped_column(nullable=True)
    sustainability_score: Mapped[float | None] = mapped_column(nullable=True)

    # Rich history arrays (JSON)
    ownership_history: Mapped[list] = mapped_column(JSON, default=list)
    refurb_history: Mapped[list] = mapped_column(JSON, default=list)
    sustainability: Mapped[dict] = mapped_column(JSON, default=dict)

    # Passport lifecycle status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
