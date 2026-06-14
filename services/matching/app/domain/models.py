"""
SQLAlchemy ORM models for the Hyperlocal Matching Service.

Owns three tables in slmai_matching:
  - match_requests   — one per return/saga (idempotent processing anchor)
  - matches          — scored buyer candidates (top matches only)
  - listings         — product listings (HYPERLOCAL or MARKETPLACE channel)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MatchRequest(Base):
    """
    Tracks the state of a hyperlocal matching attempt for a returned product.

    One record per return (idempotent — re-processing the same return_id
    returns the existing record without re-running the matching pipeline).
    """

    __tablename__ = "match_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    return_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, unique=True
    )
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    # PENDING → MATCHED | UNMATCHED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    matches: Mapped[list["Match"]] = relationship(
        "Match", back_populates="match_request", cascade="all, delete-orphan"
    )


class Match(Base):
    """
    A scored buyer candidate for a specific MatchRequest.

    Only top-scoring matches above the threshold are persisted.
    """

    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    match_request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("match_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)          # 0–100
    estimated_savings: Mapped[float] = mapped_column(Float, nullable=False)  # USD
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    match_request: Mapped["MatchRequest"] = relationship(
        "MatchRequest", back_populates="matches"
    )


class Listing(Base):
    """
    A product listing created after the matching pipeline completes.

    Channel is HYPERLOCAL if a match was found, MARKETPLACE otherwise.
    """

    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    passport_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # HYPERLOCAL | MARKETPLACE
    channel: Mapped[str] = mapped_column(String(20), nullable=False)

    # ACTIVE | RESERVED | SOLD | EXPIRED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
