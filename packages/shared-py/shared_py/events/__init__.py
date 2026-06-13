"""
shared-py/events — Redis Streams publish/subscribe wrapper + DLQ

Event-driven choreography over Redis Streams for Amazon Second Life AI.

Usage (Publishing):
    from shared_py.events import publish

    await publish(
        event_type="ProductGraded",
        correlation_id=return_id,
        data={"return_id": return_id, "grade": "A", ...},
        redis_url=settings.redis_url,
        producer=settings.service_name,
    )

Usage (Subscribing):
    from shared_py.events import subscribe, start_consumer, stop_consumer

    @subscribe(event_type="ProductGraded")
    async def handle_product_graded(envelope: EventEnvelope):
        data = ProductGradedEventData.model_validate(envelope.data)
        # ... process ...

    # In service main.py lifespan:
    consumer_task = asyncio.create_task(
        start_consumer(redis_url=settings.redis_url, group=settings.service_name)
    )
    yield
    await stop_consumer()
    consumer_task.cancel()
"""

from shared_py.events.client import close_redis, get_redis, publish
from shared_py.events.handlers import start_consumer, stop_consumer, subscribe
from shared_py.events.schemas import (
    EVENT_TYPE_TO_MODEL,
    EventEnvelope,
    HyperlocalMatchRequestedEventData,
    LifecycleDecisionCreatedEventData,
    MatchFoundEventData,
    NoMatchFoundEventData,
    PassportCreatedEventData,
    ProductGradedEventData,
    ProductListedEventData,
    PurchaseCompletedEventData,
    ReturnSubmittedEventData,
    SustainabilityUpdatedEventData,
)

__all__ = [
    # Client
    "get_redis",
    "close_redis",
    "publish",
    # Handlers
    "subscribe",
    "start_consumer",
    "stop_consumer",
    # Schemas
    "EventEnvelope",
    "EVENT_TYPE_TO_MODEL",
    "ReturnSubmittedEventData",
    "ProductGradedEventData",
    "LifecycleDecisionCreatedEventData",
    "PassportCreatedEventData",
    "HyperlocalMatchRequestedEventData",
    "MatchFoundEventData",
    "NoMatchFoundEventData",
    "ProductListedEventData",
    "PurchaseCompletedEventData",
    "SustainabilityUpdatedEventData",
]
