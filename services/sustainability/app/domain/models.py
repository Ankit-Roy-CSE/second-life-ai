"""
SQLAlchemy ORM models for the Sustainability Service.

Owns the `sustainability_records` table in `slmai_sustainability`.
One record per return, updated as new events arrive in the saga.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SustainabilityRecord(Base):
    """
    Tracks the environmental and economic impact of a single return's second life.

    One record per return (return_id is unique). Fields are updated
    incrementally as events arrive — the saga may deliver them out of order,
    so each handler performs an idempotent upsert.

    Units:
        co2_avoided_kg      — kilograms of CO₂ equivalent avoided
        waste_diverted_kg   — kilograms of product waste diverted from landfill
        value_recovered     — USD recovered through resale/donation/recycling
        green_credits       — platform credits awarded to the returner
    """

    __tablename__ = "sustainability_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    return_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, unique=True)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Calculated metrics
    co2_avoided_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    waste_diverted_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    value_recovered: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    green_credits: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Tracking which events have been processed (for idempotency)
    # PENDING → LISTED → COMPLETED
    lifecycle_stage: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
