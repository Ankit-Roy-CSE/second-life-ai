"""
Event handlers for the Product Passport Service.

Consumes:
    ProductGraded             — stores grade data in the Passport (status→GRADED)
    LifecycleDecisionCreated  — merges decision data, promotes status→ACTIVE,
                                then emits PassportCreated + HyperlocalMatchRequested

Emits:
    PassportCreated           — consumed by matching service
    HyperlocalMatchRequested  — triggers the hyperlocal matching saga step
"""

from shared_py.config import get_logger
from shared_py.events import publish, subscribe
from shared_py.events.schemas import (
    EventEnvelope,
    HyperlocalMatchRequestedEventData,
    LifecycleDecisionCreatedEventData,
    PassportCreatedEventData,
    ProductGradedEventData,
)

from app.db.session import _session_factory
from app.domain.service import PassportService

logger = get_logger(__name__)


@subscribe(event_type="ProductGraded")
async def handle_product_graded(envelope: EventEnvelope) -> None:
    """
    Consume ProductGraded → store grade data in Passport.

    Idempotent: if the Passport already has grade data for this return_id, no-ops.
    The Passport is created in GRADED status, waiting for the lifecycle decision.
    """
    correlation_id = envelope.correlation_id
    data = ProductGradedEventData.model_validate(envelope.data)

    logger.info(
        "handle_product_graded",
        extra={
            "return_id": data.return_id,
            "product_id": data.product_id,
            "grade": data.grade,
            "correlation_id": correlation_id,
        },
    )

    if _session_factory is None:
        logger.error("db_not_initialized", extra={"correlation_id": correlation_id})
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = PassportService(db)
        await service.handle_product_graded(
            return_id=data.return_id,
            product_id=data.product_id,
            user_id=data.product_id,  # user_id not in ProductGraded; use product_id as stub
            grade=data.grade,
            confidence=data.confidence,
            damage_summary=data.damage_summary,
            correlation_id=correlation_id,
        )

    logger.info(
        "passport_grade_stored",
        extra={"return_id": data.return_id, "correlation_id": correlation_id},
    )


@subscribe(event_type="LifecycleDecisionCreated")
async def handle_lifecycle_decision_created(envelope: EventEnvelope) -> None:
    """
    Consume LifecycleDecisionCreated → merge decision into Passport → emit PassportCreated
    + HyperlocalMatchRequested.

    Idempotent: if the Passport already has lifecycle data for this return_id, no-ops.
    After a successful merge, two events are emitted so the matching saga can proceed.
    """
    correlation_id = envelope.correlation_id
    data = LifecycleDecisionCreatedEventData.model_validate(envelope.data)

    logger.info(
        "handle_lifecycle_decision_created",
        extra={
            "return_id": data.return_id,
            "action": data.action,
            "correlation_id": correlation_id,
        },
    )

    if _session_factory is None:
        logger.error("db_not_initialized", extra={"correlation_id": correlation_id})
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = PassportService(db)
        passport = await service.handle_lifecycle_decision(
            return_id=data.return_id,
            action=data.action,
            value_recovery_estimate=data.value_recovery_estimate,
            sustainability_score=data.sustainability_score,
            correlation_id=correlation_id,
        )

        # Fetch the associated product to get category info for the matching event
        product = await service.get_product(passport.product_id)

    # Derive category and a stub location for matching.
    # Real product enrichment happens in P2-B3; we use sensible defaults here.
    category = product.category if product else "electronics"
    location = (
        product.attributes.get("location", {"lat": 37.7749, "lng": -122.4194, "city": "San Francisco"})
        if product
        else {"lat": 37.7749, "lng": -122.4194, "city": "San Francisco"}
    )

    from app.config import settings  # local import avoids circular import at module load

    # Emit PassportCreated
    await publish(
        event_type="PassportCreated",
        correlation_id=correlation_id,
        data=PassportCreatedEventData(
            passport_id=passport.id,
            product_id=passport.product_id,
            return_id=data.return_id,
            current_grade=passport.current_grade or "C",
        ).model_dump(mode="json"),
        redis_url=settings.redis_url,
        producer="passport",
    )

    logger.info(
        "passport_created_event_published",
        extra={
            "passport_id": passport.id,
            "return_id": data.return_id,
            "correlation_id": correlation_id,
        },
    )

    # Emit HyperlocalMatchRequested (triggers the matching saga step)
    await publish(
        event_type="HyperlocalMatchRequested",
        correlation_id=correlation_id,
        data=HyperlocalMatchRequestedEventData(
            return_id=data.return_id,
            product_id=passport.product_id,
            category=category,
            location=location,
        ).model_dump(mode="json"),
        redis_url=settings.redis_url,
        producer="passport",
    )

    logger.info(
        "hyperlocal_match_requested_event_published",
        extra={
            "return_id": data.return_id,
            "product_id": passport.product_id,
            "category": category,
            "correlation_id": correlation_id,
        },
    )
