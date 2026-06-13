"""
SQLAlchemy ORM models for the Lifecycle Decision Service.

Owns the `lifecycle_decisions` table in `slmai_lifecycle` database.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LifecycleDecision(Base):
    """
    Persisted lifecycle routing decision for a returned product.

    One decision per return (idempotent — re-processing the same return_id
    returns the existing record rather than creating a duplicate).
    """

    __tablename__ = "lifecycle_decisions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    return_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, unique=True
    )
    grade_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # AI decision output
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # RESELL / REFURBISH / DONATE / RECYCLE / HYPERLOCAL
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    value_recovery_estimate: Mapped[float] = mapped_column(Float, nullable=False)
    sustainability_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
