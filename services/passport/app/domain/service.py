"""
Product Passport business logic — pure Python, no FastAPI imports.

This module owns:
  1. Upsert Passport on ProductGraded (stores grade data, status→GRADED)
  2. Merge LifecycleDecisionCreated data and promote status→ACTIVE
  3. Expose read methods for API routes
  4. Provide data needed to emit PassportCreated + HyperlocalMatchRequested
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.config import get_logger

from app.domain.models import Passport, Product

logger = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PassportService:
    """Business logic for building and managing digital product passports."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Passport building (called from event handlers) ────────────────────────

    async def handle_product_graded(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        grade: str,
        confidence: float,
        damage_summary: str,
        correlation_id: Optional[str] = None,
    ) -> Passport:
        """
        Create or update a Passport with grading data.

        Idempotent — if the Passport already has grade data for this return_id,
        returns it unchanged.

        Args:
            return_id: UUID of the Return (saga correlation_id).
            product_id: UUID of the Product.
            user_id: UUID of the product owner.
            grade: Grade letter (A/B/C/D).
            confidence: AI confidence score 0–1.
            damage_summary: Human-readable damage description.
            correlation_id: For structured logging.

        Returns:
            Persisted Passport ORM object (status=GRADED).
        """
        corr = correlation_id or return_id

        # Ensure a canonical Product record exists
        await self._ensure_product(product_id=product_id, user_id=user_id, corr=corr)

        # Find or create the Passport for this return
        passport = await self._get_by_return_id(return_id)

        if passport is not None and passport.current_grade is not None:
            logger.info(
                "passport_grade_already_set_skipping",
                extra={"return_id": return_id, "correlation_id": corr},
            )
            return passport

        now = _utcnow()

        if passport is None:
            passport = Passport(
                id=str(uuid.uuid4()),
                return_id=return_id,
                product_id=product_id,
                current_grade=grade,
                grade_confidence=confidence,
                damage_summary=damage_summary,
                ownership_history=[
                    {
                        "event": "graded",
                        "grade": grade,
                        "confidence": confidence,
                        "timestamp": now.isoformat(),
                    }
                ],
                refurb_history=[],
                sustainability={},
                status="GRADED",
            )
            self.db.add(passport)
        else:
            # Passport exists but grade not yet set
            passport.current_grade = grade
            passport.grade_confidence = confidence
            passport.damage_summary = damage_summary
            passport.status = "GRADED"
            passport.updated_at = now
            ownership = list(passport.ownership_history or [])
            ownership.append(
                {
                    "event": "graded",
                    "grade": grade,
                    "confidence": confidence,
                    "timestamp": now.isoformat(),
                }
            )
            passport.ownership_history = ownership

        await self.db.commit()
        await self.db.refresh(passport)

        logger.info(
            "passport_grade_recorded",
            extra={
                "passport_id": passport.id,
                "grade": grade,
                "return_id": return_id,
                "correlation_id": corr,
            },
        )
        return passport

    async def handle_lifecycle_decision(
        self,
        *,
        return_id: str,
        action: str,
        value_recovery_estimate: float,
        sustainability_score: float,
        correlation_id: Optional[str] = None,
    ) -> Passport:
        """
        Merge lifecycle decision data into the Passport and promote to ACTIVE.

        Idempotent — if lifecycle data is already set for this return_id,
        returns the existing Passport unchanged.

        Args:
            return_id: UUID of the Return (saga correlation_id).
            action: Lifecycle action (RESELL/REFURBISH/DONATE/RECYCLE/HYPERLOCAL).
            value_recovery_estimate: Estimated value recovery in USD.
            sustainability_score: Sustainability score 0–100.
            correlation_id: For structured logging.

        Returns:
            Persisted Passport ORM object (status=ACTIVE).
        """
        corr = correlation_id or return_id

        passport = await self._get_by_return_id(return_id)

        if passport is None:
            # Passport not yet created — create a minimal one so we can store the decision.
            # This handles the edge case where LifecycleDecisionCreated arrives before
            # ProductGraded (event ordering is not guaranteed).
            logger.warning(
                "passport_not_found_for_lifecycle_decision_creating_stub",
                extra={"return_id": return_id, "correlation_id": corr},
            )
            passport = Passport(
                id=str(uuid.uuid4()),
                return_id=return_id,
                product_id="unknown",
                ownership_history=[],
                refurb_history=[],
                sustainability={},
                status="PENDING",
            )
            self.db.add(passport)
            await self.db.flush()

        if passport.lifecycle_action is not None:
            logger.info(
                "passport_lifecycle_already_set_skipping",
                extra={"return_id": return_id, "correlation_id": corr},
            )
            return passport

        now = _utcnow()

        passport.lifecycle_action = action
        passport.value_recovery_estimate = value_recovery_estimate
        passport.sustainability_score = sustainability_score
        passport.sustainability = {
            "score": sustainability_score,
            "action": action,
            "value_recovery_estimate": value_recovery_estimate,
        }
        passport.status = "ACTIVE"
        passport.updated_at = now

        # Append to ownership history
        ownership = list(passport.ownership_history or [])
        ownership.append(
            {
                "event": "lifecycle_decided",
                "action": action,
                "value_recovery_estimate": value_recovery_estimate,
                "sustainability_score": sustainability_score,
                "timestamp": now.isoformat(),
            }
        )
        passport.ownership_history = ownership

        # If refurb action, start a refurb history entry
        if action == "REFURBISH":
            refurb = list(passport.refurb_history or [])
            refurb.append(
                {
                    "event": "refurb_started",
                    "timestamp": now.isoformat(),
                }
            )
            passport.refurb_history = refurb

        await self.db.commit()
        await self.db.refresh(passport)

        logger.info(
            "passport_lifecycle_recorded",
            extra={
                "passport_id": passport.id,
                "action": action,
                "return_id": return_id,
                "correlation_id": corr,
            },
        )
        return passport

    # ── Reads (used by API routes) ────────────────────────────────────────────

    async def get_passport_by_id(self, passport_id: str) -> Optional[Passport]:
        """Fetch a passport by its primary key. Returns None if not found."""
        result = await self.db.execute(
            select(Passport).where(Passport.id == passport_id)
        )
        return result.scalar_one_or_none()

    async def get_passport_by_return_id(self, return_id: str) -> Optional[Passport]:
        """Fetch a passport by its return_id. Returns None if not found."""
        return await self._get_by_return_id(return_id)

    async def get_passports_by_product(
        self,
        product_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Passport], int]:
        """
        Fetch all passports for a given product_id (paginated).

        Returns:
            (items, total) tuple.
        """
        count_stmt = select(func.count(Passport.id)).where(Passport.product_id == product_id)
        list_stmt = (
            select(Passport)
            .where(Passport.product_id == product_id)
            .order_by(Passport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        items_result = await self.db.execute(list_stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Fetch the canonical Product by id. Returns None if not found."""
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_by_return_id(self, return_id: str) -> Optional[Passport]:
        result = await self.db.execute(
            select(Passport).where(Passport.return_id == return_id)
        )
        return result.scalar_one_or_none()

    async def _ensure_product(
        self, *, product_id: str, user_id: str, corr: str
    ) -> Product:
        """
        Return the existing Product record or create a minimal one if it doesn't exist.

        The Passport service owns the canonical Product entity. When another service
        (e.g. Grading) emits a ProductGraded event, the product_id is provided but
        the full Product record may not yet exist — we create a stub here so the
        passport can reference it.
        """
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

        if product is None:
            product = Product(
                id=product_id,
                owner_user_id=user_id,
                category="electronics",
                title="Returned Product",
                brand="Unknown",
                attributes={},
            )
            self.db.add(product)
            await self.db.flush()  # get the ID without committing
            logger.info(
                "product_stub_created",
                extra={"product_id": product_id, "correlation_id": corr},
            )

        return product
