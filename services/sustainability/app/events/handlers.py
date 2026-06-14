"""
Event handlers for the Sustainability Service.

Consumes:
    MatchFound        — buyer matched; update metrics with actual distance
    NoMatchFound      — no buyer; update metrics with average logistics
    ProductListed     — listing created (either channel)
    PurchaseCompleted — sale closed; finalise value and credits

Emits:
    SustainabilityUpdated — consumed by Gateway read-model
"""

from shared_py.config import get_logger
from shared_py.events import publish, subscribe
from shared_py.events.schemas import (
    EventEnvelope,
    MatchFoundEventData,
    NoMatchFoundEventData,
    ProductListedEventData,
    PurchaseCompletedEventData,
    SustainabilityUpdatedEventData,
)

from app.config import settings
from app.db.session import _session_factory
from app.domain.service import SustainabilityService

logger = get_logger(__name__)

# Defaults used when the event doesn't carry product detail
# These will be enriched in P2-B4 when value-recovery tuning lands.
_DEFAULT_CATEGORY = "electronics"
_DEFAULT_LIFECYCLE_ACTION = "RESELL"
_DEFAULT_VALUE_RECOVERED = 50.0


async def _emit_updated(record, correlation_id: str) -> None:
    """Helper: publish SustainabilityUpdated after any record change."""
    await publish(
        event_type="SustainabilityUpdated",
        correlation_id=correlation_id,
        data=SustainabilityUpdatedEventData(
            return_id=record.return_id,
            product_id=record.product_id,
            sustainability_record_id=record.id,
            co2_avoided_kg=record.co2_avoided_kg,
            waste_diverted_kg=record.waste_diverted_kg,
            value_recovered=record.value_recovered,
            green_credits=record.green_credits,
        ).model_dump(mode="json"),
        redis_url=settings.redis_url,
        producer="sustainability",
    )
    logger.info(
        "sustainability_updated_event_published",
        extra={
            "return_id": record.return_id,
            "co2": record.co2_avoided_kg,
            "credits": record.green_credits,
            "correlation_id": correlation_id,
        },
    )


@subscribe(event_type="MatchFound")
async def handle_match_found(envelope: EventEnvelope) -> None:
    """MatchFound → calculate metrics with actual buyer distance."""
    correlation_id = envelope.correlation_id
    data = MatchFoundEventData.model_validate(envelope.data)

    if _session_factory is None:
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = SustainabilityService(db)
        record = await service.process_match_found(
            return_id=data.return_id,
            product_id=data.return_id,  # product_id not in MatchFound; use correlation
            user_id=correlation_id,     # placeholder; enriched in P2-B4
            category=_DEFAULT_CATEGORY,
            lifecycle_action="HYPERLOCAL",
            value_recovered=_DEFAULT_VALUE_RECOVERED,
            distance_km=data.distance_km,
            correlation_id=correlation_id,
        )

    await _emit_updated(record, correlation_id)


@subscribe(event_type="NoMatchFound")
async def handle_no_match_found(envelope: EventEnvelope) -> None:
    """NoMatchFound → calculate metrics with average logistics distance."""
    correlation_id = envelope.correlation_id
    data = NoMatchFoundEventData.model_validate(envelope.data)

    if _session_factory is None:
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = SustainabilityService(db)
        record = await service.process_no_match_found(
            return_id=data.return_id,
            product_id=data.return_id,
            user_id=correlation_id,
            category=_DEFAULT_CATEGORY,
            lifecycle_action=_DEFAULT_LIFECYCLE_ACTION,
            value_recovered=_DEFAULT_VALUE_RECOVERED,
            correlation_id=correlation_id,
        )

    await _emit_updated(record, correlation_id)


@subscribe(event_type="ProductListed")
async def handle_product_listed(envelope: EventEnvelope) -> None:
    """ProductListed → create or update sustainability record for this listing."""
    correlation_id = envelope.correlation_id
    data = ProductListedEventData.model_validate(envelope.data)

    if _session_factory is None:
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = SustainabilityService(db)
        record = await service.process_product_listed(
            return_id=data.return_id,
            product_id=data.product_id,
            user_id=correlation_id,
            category=_DEFAULT_CATEGORY,
            lifecycle_action=_DEFAULT_LIFECYCLE_ACTION,
            value_recovered=data.price,
            correlation_id=correlation_id,
        )

    await _emit_updated(record, correlation_id)


@subscribe(event_type="PurchaseCompleted")
async def handle_purchase_completed(envelope: EventEnvelope) -> None:
    """PurchaseCompleted → finalise record with actual sale price."""
    correlation_id = envelope.correlation_id
    data = PurchaseCompletedEventData.model_validate(envelope.data)

    if _session_factory is None:
        raise RuntimeError("DB not initialised")

    async with _session_factory() as db:
        service = SustainabilityService(db)
        record = await service.process_purchase_completed(
            return_id=data.return_id,
            product_id=data.product_id,
            user_id=data.buyer_user_id,
            actual_price=data.price,
            correlation_id=correlation_id,
        )

    await _emit_updated(record, correlation_id)
