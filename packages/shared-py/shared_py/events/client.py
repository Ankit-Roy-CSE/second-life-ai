"""
Redis client singleton and event publishing for Amazon Second Life AI.

Provides:
- get_redis(): Async Redis client singleton (reused across the service lifespan).
- publish(): Publish an event to `slmai:events` with the standard envelope.

Usage:
    from shared_py.events import publish

    await publish(
        event_type="ProductGraded",
        correlation_id=return_id,
        data={
            "return_id": return_id,
            "grade": "A",
            "confidence": 0.95,
            ...
        }
    )
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from shared_py.config import get_logger
from shared_py.events.schemas import EVENT_TYPE_TO_MODEL, EventEnvelope

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Redis Client Singleton
# ═══════════════════════════════════════════════════════════════════════════

_redis_client: aioredis.Redis | None = None


async def get_redis(redis_url: str) -> aioredis.Redis:
    """
    Return the shared async Redis client singleton.

    Args:
        redis_url: Redis connection URL (e.g. "redis://redis:6379/0").

    Returns:
        Async Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("redis_client_initialized", extra={"redis_url": redis_url})
    return _redis_client


async def close_redis() -> None:
    """Close the Redis client singleton (called on service shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_client_closed")


# ═══════════════════════════════════════════════════════════════════════════
# Event Publishing
# ═══════════════════════════════════════════════════════════════════════════

STREAM_NAME = "slmai:events"


async def publish(
    event_type: str,
    correlation_id: str,
    data: dict[str, Any],
    *,
    redis_url: str,
    producer: str,
) -> str:
    """
    Publish an event to the `slmai:events` Redis stream with the standard envelope.

    Args:
        event_type: PascalCase event name (e.g. "ProductGraded").
        correlation_id: Return/saga ID threading this event through the system.
        data: Event-specific payload dictionary.
        redis_url: Redis connection URL (from service settings).
        producer: Service name emitting the event (e.g. "grading").

    Returns:
        The event_id (UUID v4 string) for idempotency tracking.

    Raises:
        ValueError: If event_type is not in the registry or data fails validation.
        redis.exceptions.RedisError: On Redis connection/operation failures.
    """
    # Validate event_type
    if event_type not in EVENT_TYPE_TO_MODEL:
        raise ValueError(
            f"Unknown event_type '{event_type}'. "
            f"Expected one of: {list(EVENT_TYPE_TO_MODEL.keys())}"
        )

    # Validate payload against the event-specific schema
    payload_model = EVENT_TYPE_TO_MODEL[event_type]
    try:
        validated_data = payload_model.model_validate(data).model_dump(mode="json")
    except Exception as e:
        logger.error(
            "event_payload_validation_failed",
            extra={
                "event_type": event_type,
                "correlation_id": correlation_id,
                "error": str(e),
            },
        )
        raise ValueError(
            f"Payload validation failed for {event_type}: {e}"
        ) from e

    # Build the envelope
    event_id = str(uuid.uuid4())
    envelope = EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        event_version="1.0",
        occurred_at=datetime.now(timezone.utc),
        correlation_id=correlation_id,
        producer=producer,
        data=validated_data,
    )

    # Serialize to JSON and publish to Redis Streams
    envelope_json = envelope.model_dump_json()
    redis_client = await get_redis(redis_url)

    try:
        await redis_client.xadd(STREAM_NAME, {"envelope": envelope_json})
        logger.info(
            "event_published",
            extra={
                "event_id": event_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
                "producer": producer,
            },
        )
    except Exception as e:
        logger.error(
            "event_publish_failed",
            extra={
                "event_id": event_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
                "error": str(e),
            },
        )
        raise

    return event_id
