"""
Event subscription and consumption for Amazon Second Life AI.

Provides:
- @subscribe() decorator: Register async handlers for specific event types.
- start_consumer(): Start the consumer loop for a service (call in lifespan).
- stop_consumer(): Gracefully shut down the consumer loop.

Handlers must be idempotent — the same event may be delivered multiple times.

Usage:
    from shared_py.events import subscribe

    @subscribe(event_type="ProductGraded")
    async def handle_product_graded(envelope: EventEnvelope):
        data = ProductGradedEventData.model_validate(envelope.data)
        # ... process the event ...
        # Raise an exception on failure — the wrapper retries and DLQs

Then in the service's main.py lifespan:
    from shared_py.events import start_consumer, stop_consumer

    @asynccontextmanager
    async def lifespan(app):
        consumer_task = asyncio.create_task(
            start_consumer(redis_url=settings.redis_url, group=settings.service_name)
        )
        yield
        await stop_consumer()
        consumer_task.cancel()
"""

import asyncio
import json
from collections.abc import Callable
from typing import Any

import redis.asyncio as aioredis

from shared_py.config import get_logger
from shared_py.events.client import STREAM_NAME, get_redis
from shared_py.events.schemas import EVENT_TYPE_TO_MODEL, EventEnvelope

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Handler Registry
# ═══════════════════════════════════════════════════════════════════════════

_handlers: dict[str, list[Callable]] = {}


def subscribe(event_type: str) -> Callable:
    """
    Decorator to register an async handler for a specific event_type.

    Args:
        event_type: PascalCase event name (e.g. "ProductGraded").

    Returns:
        The decorator function.

    Example:
        @subscribe(event_type="ProductGraded")
        async def handle_product_graded(envelope: EventEnvelope):
            data = ProductGradedEventData.model_validate(envelope.data)
            # ... do work ...
    """

    def decorator(handler: Callable) -> Callable:
        if event_type not in _handlers:
            _handlers[event_type] = []
        _handlers[event_type].append(handler)
        logger.info(
            "event_handler_registered",
            extra={"event_type": event_type, "handler": handler.__name__},
        )
        return handler

    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# Idempotency Cache (in-memory dedupe; could be Redis-backed in production)
# ═══════════════════════════════════════════════════════════════════════════

_processed_events: set[str] = set()
MAX_CACHE_SIZE = 10000


def mark_processed(event_id: str) -> None:
    """Mark an event_id as processed (for idempotency)."""
    _processed_events.add(event_id)
    # Simple FIFO eviction if cache grows too large
    if len(_processed_events) > MAX_CACHE_SIZE:
        _processed_events.pop()


def is_processed(event_id: str) -> bool:
    """Check if an event_id has already been processed."""
    return event_id in _processed_events


# ═══════════════════════════════════════════════════════════════════════════
# Consumer Loop
# ═══════════════════════════════════════════════════════════════════════════

DLQ_STREAM = "slmai:events:dlq"
MAX_RETRIES = 3
_stop_consumer = False


async def start_consumer(redis_url: str, group: str) -> None:
    """
    Start the event consumer loop for this service.

    Args:
        redis_url: Redis connection URL.
        group: Consumer group name (typically the service name, e.g. "grading").

    This function runs indefinitely until stop_consumer() is called or an
    unrecoverable error occurs. Call it as a background task in the service lifespan.
    """
    global _stop_consumer
    _stop_consumer = False

    redis_client = await get_redis(redis_url)
    consumer_name = f"{group}-worker"

    # Create the consumer group if it doesn't exist
    try:
        await redis_client.xgroup_create(
            STREAM_NAME, group, id="0", mkstream=True
        )
        logger.info(
            "consumer_group_created",
            extra={"stream": STREAM_NAME, "group": group},
        )
    except aioredis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            logger.error(
                "consumer_group_creation_failed",
                extra={"error": str(e)},
            )
            raise
        # Group already exists — continue
        logger.info(
            "consumer_group_already_exists",
            extra={"stream": STREAM_NAME, "group": group},
        )

    logger.info(
        "consumer_started",
        extra={"stream": STREAM_NAME, "group": group, "consumer": consumer_name},
    )

    # Main consumer loop
    while not _stop_consumer:
        try:
            # Read from the stream (block for 1 second if no messages)
            messages = await redis_client.xreadgroup(
                groupname=group,
                consumername=consumer_name,
                streams={STREAM_NAME: ">"},
                count=10,
                block=1000,
            )

            if not messages:
                continue

            # Process each message
            for stream_name, stream_messages in messages:
                for message_id, fields in stream_messages:
                    await _process_message(
                        redis_client=redis_client,
                        group=group,
                        stream_name=stream_name,
                        message_id=message_id,
                        fields=fields,
                    )

        except asyncio.CancelledError:
            logger.info("consumer_cancelled")
            break
        except Exception as e:
            logger.error(
                "consumer_loop_error",
                extra={"error": str(e)},
            )
            await asyncio.sleep(5)  # Back off before retrying the loop

    logger.info("consumer_stopped", extra={"group": group})


async def stop_consumer() -> None:
    """Signal the consumer loop to stop gracefully."""
    global _stop_consumer
    _stop_consumer = True
    logger.info("consumer_stop_requested")


async def _process_message(
    redis_client: aioredis.Redis,
    group: str,
    stream_name: str,
    message_id: str,
    fields: dict[str, Any],
) -> None:
    """
    Process a single message from the stream.

    Args:
        redis_client: Async Redis client.
        group: Consumer group name.
        stream_name: Name of the stream (e.g. "slmai:events").
        message_id: Redis stream message ID.
        fields: Message fields dict (contains the "envelope" JSON).
    """
    try:
        # Parse the envelope
        envelope_json = fields.get("envelope")
        if not envelope_json:
            logger.warning(
                "message_missing_envelope",
                extra={"message_id": message_id},
            )
            await redis_client.xack(stream_name, group, message_id)
            return

        envelope = EventEnvelope.model_validate_json(envelope_json)

        # Idempotency check
        if is_processed(envelope.event_id):
            logger.info(
                "event_already_processed",
                extra={
                    "event_id": envelope.event_id,
                    "event_type": envelope.event_type,
                    "correlation_id": envelope.correlation_id,
                },
            )
            await redis_client.xack(stream_name, group, message_id)
            return

        # Dispatch to registered handlers
        handlers = _handlers.get(envelope.event_type, [])
        if not handlers:
            # No handlers for this event_type in this service — ack and skip
            logger.debug(
                "no_handlers_for_event",
                extra={
                    "event_type": envelope.event_type,
                    "event_id": envelope.event_id,
                },
            )
            await redis_client.xack(stream_name, group, message_id)
            mark_processed(envelope.event_id)
            return

        # Execute all handlers for this event_type
        for handler in handlers:
            try:
                await handler(envelope)
                logger.info(
                    "event_handled",
                    extra={
                        "event_id": envelope.event_id,
                        "event_type": envelope.event_type,
                        "correlation_id": envelope.correlation_id,
                        "handler": handler.__name__,
                    },
                )
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    extra={
                        "event_id": envelope.event_id,
                        "event_type": envelope.event_type,
                        "correlation_id": envelope.correlation_id,
                        "handler": handler.__name__,
                        "error": str(e),
                    },
                )
                # On handler failure, check retry count and DLQ if needed
                await _handle_failure(
                    redis_client=redis_client,
                    group=group,
                    stream_name=stream_name,
                    message_id=message_id,
                    envelope=envelope,
                )
                return  # Don't ack — let it retry

        # All handlers succeeded — mark processed and ack
        mark_processed(envelope.event_id)
        await redis_client.xack(stream_name, group, message_id)

    except Exception as e:
        logger.error(
            "message_processing_error",
            extra={"message_id": message_id, "error": str(e)},
        )
        # Don't ack — let it retry


async def _handle_failure(
    redis_client: aioredis.Redis,
    group: str,
    stream_name: str,
    message_id: str,
    envelope: EventEnvelope,
) -> None:
    """
    Handle a failed message by checking delivery count and DLQing if needed.

    Args:
        redis_client: Async Redis client.
        group: Consumer group name.
        stream_name: Name of the stream.
        message_id: Redis stream message ID.
        envelope: Parsed event envelope.
    """
    # Get the pending entry info to check delivery count
    try:
        pending = await redis_client.xpending_range(
            stream_name, group, min=message_id, max=message_id, count=1
        )
        if not pending:
            return

        delivery_count = pending[0]["times_delivered"]

        if delivery_count >= MAX_RETRIES:
            # Too many retries — dead-letter the message
            logger.warning(
                "event_dead_lettered",
                extra={
                    "event_id": envelope.event_id,
                    "event_type": envelope.event_type,
                    "correlation_id": envelope.correlation_id,
                    "delivery_count": delivery_count,
                },
            )
            # Move to DLQ
            envelope_json = envelope.model_dump_json()
            await redis_client.xadd(DLQ_STREAM, {"envelope": envelope_json})
            # Ack the original message so it stops redelivering
            await redis_client.xack(stream_name, group, message_id)
            mark_processed(envelope.event_id)
        else:
            # Let it retry — don't ack
            logger.info(
                "event_will_retry",
                extra={
                    "event_id": envelope.event_id,
                    "event_type": envelope.event_type,
                    "delivery_count": delivery_count,
                    "max_retries": MAX_RETRIES,
                },
            )
    except Exception as e:
        logger.error(
            "failure_handling_error",
            extra={"message_id": message_id, "error": str(e)},
        )
