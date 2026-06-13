"""
Grading business logic — pure Python, no FastAPI imports.

This module owns the core grading workflow:
  1. Call AI wrapper to grade the product
  2. Persist the Grade record
  3. Return the result (caller is responsible for emitting the event)
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.ai import ai_client
from shared_py.config import get_logger
from shared_py.schemas.enums import Grade as GradeEnum

from app.domain.models import Grade
from app.domain.schemas import GradeResponse

logger = get_logger(__name__)


class GradingService:
    """Business logic for AI-powered product grading."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def grade_product(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        return_reason: str,
        media_keys: list[str],
        product_category: str = "electronics",
        correlation_id: Optional[str] = None,
    ) -> Grade:
        """
        Run AI grading for a returned product and persist the result.

        Idempotent: if a Grade already exists for return_id, returns it
        without re-calling the AI (prevents double-processing the same event).

        Args:
            return_id: UUID of the Return (also the saga correlation_id).
            product_id: UUID of the Product.
            user_id: UUID of the User.
            return_reason: Customer's stated return reason.
            media_keys: S3/MinIO object keys for product images/videos.
            product_category: Product category for AI context.
            correlation_id: For structured logging.

        Returns:
            Persisted Grade ORM object.
        """
        corr = correlation_id or return_id

        # Idempotency check — return existing grade if already processed
        existing = await self._get_by_return_id(return_id)
        if existing:
            logger.info(
                "grade_already_exists_skipping",
                extra={"return_id": return_id, "correlation_id": corr},
            )
            return existing

        # Call AI wrapper
        logger.info(
            "grading_product",
            extra={"return_id": return_id, "correlation_id": corr, "media_count": len(media_keys)},
        )

        ai_result = await ai_client.grade_product(
            media_keys=media_keys,
            return_reason=return_reason,
            product_category=product_category,
            correlation_id=corr,
        )

        # Build ORM record
        grade_id = str(uuid.uuid4())
        grade = Grade(
            id=grade_id,
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade=ai_result.grade.value,
            confidence=ai_result.confidence,
            damage_summary=ai_result.damage_summary.text,
            key_points=ai_result.damage_summary.key_points,
            defects=[
                {
                    "name": d.name,
                    "severity": d.severity,
                    "location": d.location,
                    "confidence": d.confidence,
                }
                for d in ai_result.defects
            ],
            model_version=ai_result.model_version,
            return_reason=return_reason,
            media_keys=media_keys,
        )

        self.db.add(grade)
        await self.db.commit()
        await self.db.refresh(grade)

        logger.info(
            "grading_complete",
            extra={
                "grade_id": grade_id,
                "grade": ai_result.grade.value,
                "confidence": ai_result.confidence,
                "correlation_id": corr,
            },
        )

        return grade

    async def get_grade_by_return_id(self, return_id: str) -> Optional[Grade]:
        """Fetch a grade by its return_id. Returns None if not found."""
        return await self._get_by_return_id(return_id)

    async def _get_by_return_id(self, return_id: str) -> Optional[Grade]:
        result = await self.db.execute(
            select(Grade).where(Grade.return_id == return_id)
        )
        return result.scalar_one_or_none()
