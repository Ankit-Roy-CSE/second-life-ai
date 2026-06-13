"""
Event handlers for the Lifecycle Decision Service.

Consumes:
    ProductGraded — triggers lifecycle decision, persists LifecycleDecision,
                    emits LifecycleDecisionCreated

Emits:
    LifecycleDecisionCreated — consumed by passport and matching services
"""

from shared_py.config import get_logger
from shared_py.events import publish, subscribe
from shared_py.events.schemas import (
    EventEnvelope,
    LifecycleDecisionCreatedEventData,
    ProductGradedEventData,
)

from app.db.session import _session_factory
from app.domain.service import LifecycleService

logger = get_logger(__name__)


@subscribe(event_type="ProductGraded")
async def handle_product_graded(envelope: EventEnvelope) -> None:
    """
    Consume ProductGraded → run AI lifecycle decision → emit LifecycleDecisionCreated.

    This handler is idempotent: if a LifecycleDecision already exists for the return_id
    the LifecycleService returns the existing record without re-calling AI.
    """
    correlation_id = envelope.correlation_id
    data = ProductGradedEventData.model_validate(envelope.data)

    logger.info(
        "handle_product_graded",
        extra={
            "return_id": data.return_id,
            "grade": data.grade,
            "grade_id": data.grade_id,
            "correlation_id": correlation_id,
        },
    )

    if _session_factory is None:
        logger.error(
            "db_not_initialized",
            extra={"correlation_id": correlation_id},
        )
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = LifecycleService(db)

        decision = await service.decide_lifecycle(
            return_id=data.return_id,
            grade_id=data.grade_id,
            grade=data.grade,
            # Default category and value until enrichment pipeline (P2-B3)
            product_category="electronics",
            value_estimate=100.0,
            correlation_id=correlation_id,
        )

    # Emit LifecycleDecisionCreated event
    from app.config import settings  # local import avoids circular import at module load

    await publish(
        event_type="LifecycleDecisionCreated",
        correlation_id=correlation_id,
        data=LifecycleDecisionCreatedEventData(
            return_id=data.return_id,
            decision_id=decision.id,
            grade_id=data.grade_id,
            action=decision.action,
            rationale=decision.rationale,
            value_recovery_estimate=decision.value_recovery_estimate,
            sustainability_score=decision.sustainability_score,
        ).model_dump(mode="json"),
        redis_url=settings.redis_url,
        producer="lifecycle",
    )

    logger.info(
        "lifecycle_decision_created_event_published",
        extra={
            "decision_id": decision.id,
            "action": decision.action,
            "return_id": data.return_id,
            "correlation_id": correlation_id,
        },
    )
