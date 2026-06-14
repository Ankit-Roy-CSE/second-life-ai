"""
Event handlers for the Hyperlocal Matching Service.

Consumes:
    HyperlocalMatchRequested — triggers buyer matching, persists MatchRequest / Match / Listing,
                               emits MatchFound | NoMatchFound and ProductListed

Emits:
    MatchFound        — consumed by sustainability, passport services
    NoMatchFound      — consumed by sustainability service
    ProductListed     — consumed by sustainability service
"""

from shared_py.config import get_logger
from shared_py.events import publish, subscribe
from shared_py.events.schemas import (
    EventEnvelope,
    HyperlocalMatchRequestedEventData,
    MatchFoundEventData,
    NoMatchFoundEventData,
    ProductListedEventData,
)

from app.config import settings
from app.db.session import _session_factory
from app.domain.service import MatchingService

logger = get_logger(__name__)

# Default price used when no price is available in the event payload.
# TODO: enrich with actual pricing from the Product/Passport service (P2-B3).
_DEFAULT_PRICE = 50.0
_DEFAULT_PASSPORT_ID = "unknown"


@subscribe(event_type="HyperlocalMatchRequested")
async def handle_hyperlocal_match_requested(envelope: EventEnvelope) -> None:
    """
    Consume HyperlocalMatchRequested → run buyer matching → emit MatchFound|NoMatchFound + ProductListed.

    Idempotent: if a MatchRequest already exists for the return_id the handler
    skips re-processing and returns early.
    """
    correlation_id = envelope.correlation_id
    data = HyperlocalMatchRequestedEventData.model_validate(envelope.data)

    logger.info(
        "handle_hyperlocal_match_requested",
        extra={
            "return_id": data.return_id,
            "product_id": data.product_id,
            "category": data.category,
            "correlation_id": correlation_id,
        },
    )

    if _session_factory is None:
        logger.error("db_not_initialized", extra={"correlation_id": correlation_id})
        raise RuntimeError("DB not initialised")

    # Extract lat/lng from location dict
    location = data.location or {}
    lat: float = float(location.get("lat", 0.0))
    lng: float = float(location.get("lng", 0.0))

    # Passport ID may be forwarded in future; use placeholder for now.
    passport_id: str = str(location.get("passport_id", _DEFAULT_PASSPORT_ID))
    price: float = float(location.get("price", _DEFAULT_PRICE))

    async with _session_factory() as db:
        service = MatchingService(
            db=db,
            user_service_url=settings.user_service_url,
            radius_km=settings.match_radius_km,
            score_threshold=settings.match_score_threshold,
        )

        best_match, listing = await service.run_matching(
            return_id=data.return_id,
            product_id=data.product_id,
            category=data.category,
            lat=lat,
            lng=lng,
            passport_id=passport_id,
            price=price,
            correlation_id=correlation_id,
        )

    # ── Emit MatchFound or NoMatchFound ──────────────────────────────────────
    if best_match is not None:
        await publish(
            event_type="MatchFound",
            correlation_id=correlation_id,
            data=MatchFoundEventData(
                return_id=data.return_id,
                match_request_id=best_match.match_request_id,
                buyer_user_id=best_match.buyer_user_id,
                score=best_match.score,
                estimated_savings=best_match.estimated_savings,
                distance_km=best_match.distance_km,
            ).model_dump(mode="json"),
            redis_url=settings.redis_url,
            producer="matching",
        )
        logger.info(
            "match_found_event_published",
            extra={
                "match_id": best_match.id,
                "buyer_user_id": best_match.buyer_user_id,
                "score": best_match.score,
                "correlation_id": correlation_id,
            },
        )
    else:
        await publish(
            event_type="NoMatchFound",
            correlation_id=correlation_id,
            data=NoMatchFoundEventData(
                return_id=data.return_id,
                match_request_id=listing.id,  # best proxy; no match_request_id on listing
                reason="No nearby buyers found above the score threshold",
            ).model_dump(mode="json"),
            redis_url=settings.redis_url,
            producer="matching",
        )
        logger.info(
            "no_match_found_event_published",
            extra={"return_id": data.return_id, "correlation_id": correlation_id},
        )

    # ── Emit ProductListed ───────────────────────────────────────────────────
    await publish(
        event_type="ProductListed",
        correlation_id=correlation_id,
        data=ProductListedEventData(
            listing_id=listing.id,
            product_id=data.product_id,
            return_id=data.return_id,
            channel=listing.channel,
            price=listing.price,
            status=listing.status,
        ).model_dump(mode="json"),
        redis_url=settings.redis_url,
        producer="matching",
    )
    logger.info(
        "product_listed_event_published",
        extra={
            "listing_id": listing.id,
            "channel": listing.channel,
            "correlation_id": correlation_id,
        },
    )
