"""
Lifecycle Decision business logic — pure Python, no FastAPI imports.

This module owns the core lifecycle decision workflow:
  1. Call AI wrapper to decide the optimal lifecycle action
  2. Persist the LifecycleDecision record
  3. Return the result (caller is responsible for emitting the event)
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.ai import ai_client
from shared_py.config import get_logger
from shared_py.schemas.enums import Grade as GradeEnum

from app.domain.models import LifecycleDecision

logger = get_logger(__name__)


class LifecycleService:
    """Business logic for AI-powered lifecycle routing decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def decide_lifecycle(
        self,
        *,
        return_id: str,
        grade_id: str,
        grade: str,
        product_category: str = "electronics",
        value_estimate: float = 100.0,
        correlation_id: Optional[str] = None,
    ) -> LifecycleDecision:
        """
        Run AI lifecycle decision for a graded product and persist the result.

        Idempotent: if a LifecycleDecision already exists for return_id, returns it
        without re-calling the AI (prevents double-processing the same event).

        Args:
            return_id: UUID of the Return (also the saga correlation_id).
            grade_id: UUID of the Grade entity that triggered this decision.
            grade: Product condition grade (A/B/C/D).
            product_category: Product category for AI context.
            value_estimate: Estimated product value in USD.
            correlation_id: For structured logging.

        Returns:
            Persisted LifecycleDecision ORM object.
        """
        corr = correlation_id or return_id

        # Idempotency check — return existing decision if already processed
        existing = await self._get_by_return_id(return_id)
        if existing:
            logger.info(
                "decision_already_exists_skipping",
                extra={"return_id": return_id, "correlation_id": corr},
            )
            return existing

        # Call AI wrapper
        logger.info(
            "deciding_lifecycle",
            extra={
                "return_id": return_id,
                "grade": grade,
                "correlation_id": corr,
            },
        )

        # Convert string grade to enum for the AI client
        grade_enum = GradeEnum(grade)

        ai_result = await ai_client.decide_lifecycle(
            grade=grade_enum,
            product_category=product_category,
            value_estimate=value_estimate,
            correlation_id=corr,
        )

        # Build ORM record
        decision_id = str(uuid.uuid4())
        decision = LifecycleDecision(
            id=decision_id,
            return_id=return_id,
            grade_id=grade_id,
            action=ai_result.action.value,
            rationale=ai_result.rationale,
            value_recovery_estimate=ai_result.value_recovery_estimate,
            sustainability_score=ai_result.sustainability_score,
        )

        self.db.add(decision)
        await self.db.commit()
        await self.db.refresh(decision)

        logger.info(
            "lifecycle_decision_complete",
            extra={
                "decision_id": decision_id,
                "action": ai_result.action.value,
                "value_recovery": ai_result.value_recovery_estimate,
                "sustainability_score": ai_result.sustainability_score,
                "correlation_id": corr,
            },
        )

        return decision

    async def get_decision_by_return_id(self, return_id: str) -> Optional[LifecycleDecision]:
        """Fetch a decision by its return_id. Returns None if not found."""
        return await self._get_by_return_id(return_id)

    async def _get_by_return_id(self, return_id: str) -> Optional[LifecycleDecision]:
        result = await self.db.execute(
            select(LifecycleDecision).where(LifecycleDecision.return_id == return_id)
        )
        return result.scalar_one_or_none()
