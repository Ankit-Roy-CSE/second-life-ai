"""
SQLAlchemy ORM models for Gateway Service.

Gateway owns the Return entity (see architecture.md §5).
This is the only database table the Gateway manages.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all Gateway models."""

    pass


class Return(Base):
    """
    Return entity — owns the product return lifecycle.

    Gateway creates this entity when a user submits a return (POST /returns).
    The return flows through the event saga, updating status at each step.

    Key fields:
    - id: UUID v4 string (PK) — also the correlation_id for the event saga
    - product_id: UUID of the Product being returned (owned by Passport service)
    - user_id: UUID of the User who submitted the return
    - reason: User-provided text explaining why they're returning the product
    - media: JSON array of S3/MinIO object keys for uploaded images/videos
    - status: ReturnStatus enum (SUBMITTED → GRADED → DECIDED → ... → SOLD/FAILED)
    - created_at: UTC timestamp
    """

    __tablename__ = "returns"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Media files (S3 keys) as JSON array
    media: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Status from ReturnStatus enum
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="SUBMITTED", index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Return(id={self.id}, product_id={self.product_id}, status={self.status})>"
