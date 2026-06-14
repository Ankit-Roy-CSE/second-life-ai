"""
Event handlers for the AI Grading Service.

Consumes:
    ReturnSubmitted — triggers AI grading, persists Grade, emits ProductGraded

Emits:
    ProductGraded — consumed by lifecycle and passport services
"""

import uuid

from shared_py.config import get_logger
from shared_py.events import publish, subscribe
from shared_py.events.schemas import (
    EventEnvelope,
    ProductGradedEventData,
    ReturnSubmittedEventData,
)

import app.db.session as db_module
from app.domain.service import GradingService

logger = get_logger(__name__)


@subscribe(event_type="ReturnSubmitted")
async def handle_return_submitted(envelope: EventEnvelope) -> None:
    """
    Consume ReturnSubmitted → run AI grading → emit ProductGraded.

    This handler is idempotent: if a Grade already exists for the return_id
    the GradingService returns the existing record without re-calling AI.
    """
    correlation_id = envelope.correlation_id
    data = ReturnSubmittedEventData.model_validate(envelope.data)

    logger.info(
        "handle_return_submitted",
        extra={
            "return_id": data.return_id,
            "product_id": data.product_id,
            "correlation_id": correlation_id,
            "media_count": len(data.media),
        },
    )

    if db_module._session_factory is None:
        logger.error(
            "db_not_initialized",
            extra={"correlation_id": correlation_id},
        )
        raise RuntimeError("DB not initialised")

    async with db_module._session_factory() as db:
        service = GradingService(db)

        grade = await service.grade_product(
            return_id=data.return_id,
            product_id=data.product_id,
            user_id=data.user_id,
            return_reason=data.reason,
            media_keys=data.media,
            # Use product_id suffix as a rough category proxy until P2-B3 enrichment
            # Real category comes from Passport Service in a future phase
            product_category="electronics",
            correlation_id=correlation_id,
        )

    # Emit ProductGraded event
    from app.config import settings  # local import avoids circular import at module load

    await publish(
        event_type="ProductGraded",
        correlation_id=correlation_id,
        data=ProductGradedEventData(
            return_id=data.return_id,
            grade_id=grade.id,
            product_id=data.product_id,
            grade=grade.grade,
            confidence=grade.confidence,
            damage_summary=grade.damage_summary,
            defects=[d["name"] for d in grade.defects],
        ).model_dump(mode="json"),
        redis_url=settings.redis_url,
        producer="grading",
    )

    logger.info(
        "product_graded_event_published",
        extra={
            "grade_id": grade.id,
            "grade": grade.grade,
            "return_id": data.return_id,
            "correlation_id": correlation_id,
        },
    )
