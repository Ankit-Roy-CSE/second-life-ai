"""
Sustainability business logic — pure Python, no FastAPI imports.

Handles upsert logic: records are created on first event and updated
as the saga progresses. All metric calculations are delegated to calculator.py.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.config import get_logger

from app.domain.calculator import calculate_metrics
from app.domain.models import SustainabilityRecord
from app.domain.schemas import SustainabilityMetricsResponse

logger = get_logger(__name__)


class SustainabilityService:
    """Business logic for sustainability impact tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    # Write methods (called by event handlers)
    # ─────────────────────────────────────────────────────────────────────────

    async def process_match_found(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        category: str,
        lifecycle_action: str,
        value_recovered: float,
        distance_km: float,
        correlation_id: Optional[str] = None,
    ) -> SustainabilityRecord:
        """
        Handle MatchFound — hyperlocal match, shortest logistics chain.

        Creates or updates the SustainabilityRecord with metrics derived
        from the actual buyer distance.
        """
        metrics = calculate_metrics(
            category=category,
            lifecycle_action=lifecycle_action,
            value_recovered=value_recovered,
            distance_km=distance_km,
        )
        return await self._upsert(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            lifecycle_stage="MATCHED",
            metrics=metrics,
            correlation_id=correlation_id,
        )

    async def process_no_match_found(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        category: str,
        lifecycle_action: str,
        value_recovered: float,
        correlation_id: Optional[str] = None,
    ) -> SustainabilityRecord:
        """
        Handle NoMatchFound — marketplace route, average logistics distance.
        """
        metrics = calculate_metrics(
            category=category,
            lifecycle_action=lifecycle_action,
            value_recovered=value_recovered,
            distance_km=None,  # uses average
        )
        return await self._upsert(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            lifecycle_stage="LISTED",
            metrics=metrics,
            correlation_id=correlation_id,
        )

    async def process_product_listed(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        category: str,
        lifecycle_action: str,
        value_recovered: float,
        correlation_id: Optional[str] = None,
    ) -> SustainabilityRecord:
        """
        Handle ProductListed — updates stage to LISTED if not already further along.
        Only updates metrics if no record exists yet (e.g. NoMatchFound didn't run).
        """
        existing = await self._get_by_return_id(return_id)
        if existing and existing.lifecycle_stage in ("MATCHED", "COMPLETED"):
            logger.info(
                "sustainability_skip_product_listed_already_processed",
                extra={"return_id": return_id, "stage": existing.lifecycle_stage},
            )
            return existing

        metrics = calculate_metrics(
            category=category,
            lifecycle_action=lifecycle_action,
            value_recovered=value_recovered,
            distance_km=None,
        )
        return await self._upsert(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            lifecycle_stage="LISTED",
            metrics=metrics,
            correlation_id=correlation_id,
        )

    async def process_purchase_completed(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        actual_price: float,
        correlation_id: Optional[str] = None,
    ) -> SustainabilityRecord:
        """
        Handle PurchaseCompleted — finalises the record with actual sale price.

        Updates value_recovered to the actual transaction price and recalculates
        green credits. Stage advances to COMPLETED.
        """
        existing = await self._get_by_return_id(return_id)
        if existing is None:
            # Record may not exist if matching events were lost; create a stub
            logger.warning(
                "sustainability_record_not_found_for_purchase",
                extra={"return_id": return_id, "correlation_id": correlation_id},
            )
            # Create a minimal stub — enough to emit SustainabilityUpdated
            existing = SustainabilityRecord(
                id=str(uuid.uuid4()),
                return_id=return_id,
                product_id=product_id,
                user_id=user_id,
                lifecycle_stage="PENDING",
            )
            self.db.add(existing)
            await self.db.flush()

        # Recalculate with actual price
        from app.domain.calculator import calculate_green_credits
        new_credits = calculate_green_credits(
            co2_avoided_kg=existing.co2_avoided_kg,
            value_recovered=actual_price,
        )
        existing.value_recovered = round(actual_price, 2)
        existing.green_credits = new_credits
        existing.lifecycle_stage = "COMPLETED"

        await self.db.commit()
        await self.db.refresh(existing)

        logger.info(
            "sustainability_purchase_completed",
            extra={
                "return_id": return_id,
                "value_recovered": actual_price,
                "green_credits": new_credits,
                "correlation_id": correlation_id,
            },
        )
        return existing

    # ─────────────────────────────────────────────────────────────────────────
    # Read methods (used by REST routes)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_record_by_id(self, record_id: str) -> Optional[SustainabilityRecord]:
        result = await self.db.execute(
            select(SustainabilityRecord).where(SustainabilityRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_record_by_return_id(self, return_id: str) -> Optional[SustainabilityRecord]:
        return await self._get_by_return_id(return_id)

    async def list_records(
        self,
        return_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SustainabilityRecord], int]:
        filters = []
        if return_id:
            filters.append(SustainabilityRecord.return_id == return_id)
        if user_id:
            filters.append(SustainabilityRecord.user_id == user_id)

        count_stmt = select(func.count(SustainabilityRecord.id))
        list_stmt = select(SustainabilityRecord).order_by(
            SustainabilityRecord.created_at.desc()
        )
        for f in filters:
            count_stmt = count_stmt.where(f)
            list_stmt = list_stmt.where(f)

        total = (await self.db.execute(count_stmt)).scalar_one()
        items = (
            await self.db.execute(list_stmt.limit(limit).offset(offset))
        ).scalars().all()

        return list(items), total

    async def get_metrics(
        self, user_id: Optional[str] = None
    ) -> SustainabilityMetricsResponse:
        """Aggregate totals for the dashboard."""
        records, total = await self.list_records(user_id=user_id, limit=1000, offset=0)

        return SustainabilityMetricsResponse(
            total_co2_avoided_kg=round(sum(r.co2_avoided_kg for r in records), 4),
            total_waste_diverted_kg=round(sum(r.waste_diverted_kg for r in records), 4),
            total_value_recovered=round(sum(r.value_recovered for r in records), 2),
            total_green_credits=round(sum(r.green_credits for r in records), 2),
            total_returns_processed=total,
            records=records,  # type: ignore[arg-type]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_by_return_id(
        self, return_id: str
    ) -> Optional[SustainabilityRecord]:
        result = await self.db.execute(
            select(SustainabilityRecord).where(
                SustainabilityRecord.return_id == return_id
            )
        )
        return result.scalar_one_or_none()

    async def _upsert(
        self,
        *,
        return_id: str,
        product_id: str,
        user_id: str,
        lifecycle_stage: str,
        metrics: dict[str, float],
        correlation_id: Optional[str] = None,
    ) -> SustainabilityRecord:
        """
        Insert or update a SustainabilityRecord.

        If no record exists, creates one. If one exists, updates only
        if the new lifecycle_stage is equal or later in the pipeline.
        """
        existing = await self._get_by_return_id(return_id)

        if existing is None:
            record = SustainabilityRecord(
                id=str(uuid.uuid4()),
                return_id=return_id,
                product_id=product_id,
                user_id=user_id,
                lifecycle_stage=lifecycle_stage,
                **metrics,
            )
            self.db.add(record)
        else:
            # Always overwrite metrics (last-writer wins; events are idempotent)
            existing.co2_avoided_kg = metrics["co2_avoided_kg"]
            existing.waste_diverted_kg = metrics["waste_diverted_kg"]
            existing.value_recovered = metrics["value_recovered"]
            existing.green_credits = metrics["green_credits"]
            existing.lifecycle_stage = lifecycle_stage
            record = existing

        await self.db.commit()
        await self.db.refresh(record)

        logger.info(
            "sustainability_record_upserted",
            extra={
                "return_id": return_id,
                "stage": lifecycle_stage,
                "co2": metrics["co2_avoided_kg"],
                "credits": metrics["green_credits"],
                "correlation_id": correlation_id,
            },
        )
        return record
