"""
SQLAlchemy ORM models for the AI Grading Service.

Owns the `grades` table in `slmai_grading` database.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Grade(Base):
    """
    Persisted result of an AI grading run for a returned product.

    One Grade per return (idempotent — re-processing the same return_id
    updates the existing row via upsert rather than creating a duplicate).
    """

    __tablename__ = "grades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, unique=True)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # AI grading output
    grade: Mapped[str] = mapped_column(String(1), nullable=False)          # A / B / C / D
    confidence: Mapped[float] = mapped_column(Float, nullable=False)        # 0.0–1.0
    damage_summary: Mapped[str] = mapped_column(Text, nullable=False)       # human-readable text
    key_points: Mapped[list] = mapped_column(JSON, default=list)            # bullet-point list
    defects: Mapped[list] = mapped_column(JSON, default=list)               # list of defect dicts
    model_version: Mapped[str] = mapped_column(String(50), default="mock-v1")

    # Input context (stored for auditability)
    return_reason: Mapped[str] = mapped_column(Text, nullable=False)
    media_keys: Mapped[list] = mapped_column(JSON, default=list)            # S3 keys

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
