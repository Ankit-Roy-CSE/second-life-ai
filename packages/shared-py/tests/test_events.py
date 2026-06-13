"""
Tests for the shared-py events wrapper (Redis Streams pub/sub + DLQ).

Tests cover:
- Event publishing with envelope construction and validation
- Event subscription and consumption with idempotency
- Handler success and failure paths
- Retry logic and dead-letter queueing after max retries
- Multiple handlers for the same event type
"""

import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared_py.events import (
    EVENT_TYPE_TO_MODEL,
    EventEnvelope,
    ProductGradedEventData,
    ReturnSubmittedEventData,
    close_redis,
    publish,
    start_consumer,
    stop_consumer,
    subscribe,
)
from shared_py.events.client import STREAM_NAME
from shared_py.events.handlers import (
    DLQ_STREAM,
    _handlers,
    _processed_events,
    is_processed,
    mark_processed,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    _handlers.clear()
    _processed_events.clear()
    yield
    _handlers.clear()
    _processed_events.clear()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.xadd = AsyncMock(return_value=b"1234567890-0")
    mock.xreadgroup = AsyncMock(return_value=[])
    mock.xgroup_create = AsyncMock()
    mock.xack = AsyncMock()
    mock.xpending_range = AsyncMock(return_value=[])
    mock.aclose = AsyncMock()
    return mock


# ═══════════════════════════════════════════════════════════════════════════
# Publishing Tests
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_publish_valid_event(mock_redis):
    """Test publishing a valid event builds the envelope and writes to Redis."""
    with patch("shared_py.events.client.get_redis", return_value=mock_redis):
        event_id = await publish(
            event_type="ReturnSubmitted",
            correlation_id="return-123",
            data={
                "return_id": "return-123",
                "product_id": "product-456",
                "user_id": "user-789",
                "reason": "Defective",
                "media": ["s3://bucket/image1.jpg"],
            },
            redis_url="redis://localhost:6379/0",
            producer="gateway",
        )

        # Should return a UUID event_id
        assert uuid.UUID(event_id)

        # Should call xadd with the stream name and envelope JSON
        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == STREAM_NAME
        envelope_json = call_args[0][1]["envelope"]

        # Parse and validate the envelope
        envelope = EventEnvelope.model_validate_json(envelope_json)
        assert envelope.event_id == event_id
        assert envelope.event_type == "ReturnSubmitted"
        assert envelope.correlation_id == "return-123"
        assert envelope.producer == "gateway"
        assert envelope.data["return_id"] == "return-123"


@pytest.mark.asyncio
async def test_publish_invalid_event_type(mock_redis):
    """Test publishing with an unknown event_type raises ValueError."""
    with patch("shared_py.events.client.get_redis", return_value=mock_redis):
        with pytest.raises(ValueError, match="Unknown event_type"):
            await publish(
                event_type="InvalidEventType",
                correlation_id="return-123",
                data={},
                redis_url="redis://localhost:6379/0",
                producer="gateway",
            )


@pytest.mark.asyncio
async def test_publish_invalid_payload(mock_redis):
    """Test publishing with an invalid payload raises ValueError."""
    with patch("shared_py.events.client.get_redis", return_value=mock_redis):
        with pytest.raises(ValueError, match="Payload validation failed"):
            await publish(
                event_type="ReturnSubmitted",
                correlation_id="return-123",
                data={
                    # Missing required fields
                    "return_id": "return-123",
                },
                redis_url="redis://localhost:6379/0",
                producer="gateway",
            )


# ═══════════════════════════════════════════════════════════════════════════
# Subscription and Idempotency Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_subscribe_registers_handler():
    """Test that @subscribe registers the handler in the global registry."""

    @subscribe(event_type="ProductGraded")
    async def my_handler(envelope):
        pass

    assert "ProductGraded" in _handlers
    assert my_handler in _handlers["ProductGraded"]


def test_idempotency_marking():
    """Test that mark_processed and is_processed work correctly."""
    event_id = "test-event-123"
    assert not is_processed(event_id)

    mark_processed(event_id)
    assert is_processed(event_id)


@pytest.mark.asyncio
async def test_consumer_processes_event(mock_redis):
    """Test the consumer loop processes an event and calls the handler."""
    handler_called = asyncio.Event()
    received_envelope = None

    @subscribe(event_type="ProductGraded")
    async def test_handler(envelope: EventEnvelope):
        nonlocal received_envelope
        received_envelope = envelope
        handler_called.set()

    # Build a test message
    test_envelope = EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type="ProductGraded",
        event_version="1.0",
        occurred_at=datetime.utcnow(),
        correlation_id="return-123",
        producer="grading",
        data={
            "return_id": "return-123",
            "grade_id": "grade-456",
            "product_id": "product-789",
            "grade": "A",
            "confidence": 0.95,
            "damage_summary": "Minor scratches",
            "defects": ["scratch"],
        },
    )
    envelope_json = test_envelope.model_dump_json()

    # Mock xreadgroup to return our test message once, then stop
    message_returned = False

    async def mock_xreadgroup(*args, **kwargs):
        nonlocal message_returned
        if not message_returned:
            message_returned = True
            return [
                (
                    STREAM_NAME,
                    [("1234567890-0", {"envelope": envelope_json})],
                )
            ]
        # After returning the message once, simulate no more messages
        await asyncio.sleep(0.1)
        return []

    mock_redis.xreadgroup.side_effect = mock_xreadgroup

    with patch("shared_py.events.handlers.get_redis", return_value=mock_redis):
        # Start consumer in background
        consumer_task = asyncio.create_task(
            start_consumer(redis_url="redis://localhost:6379/0", group="test-service")
        )

        # Wait for handler to be called (with timeout)
        try:
            await asyncio.wait_for(handler_called.wait(), timeout=2.0)
        finally:
            await stop_consumer()
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

    # Verify handler was called with correct envelope
    assert received_envelope is not None
    assert received_envelope.event_id == test_envelope.event_id
    assert received_envelope.event_type == "ProductGraded"
    assert received_envelope.correlation_id == "return-123"

    # Verify message was acked
    mock_redis.xack.assert_called()


@pytest.mark.asyncio
async def test_consumer_idempotency_skip_processed(mock_redis):
    """Test that already-processed events are skipped."""
    handler_call_count = 0

    @subscribe(event_type="ProductGraded")
    async def test_handler(envelope: EventEnvelope):
        nonlocal handler_call_count
        handler_call_count += 1

    event_id = str(uuid.uuid4())
    test_envelope = EventEnvelope(
        event_id=event_id,
        event_type="ProductGraded",
        event_version="1.0",
        occurred_at=datetime.utcnow(),
        correlation_id="return-123",
        producer="grading",
        data={
            "return_id": "return-123",
            "grade_id": "grade-456",
            "product_id": "product-789",
            "grade": "A",
            "confidence": 0.95,
            "damage_summary": "Minor scratches",
            "defects": [],
        },
    )
    envelope_json = test_envelope.model_dump_json()

    # Mark as already processed
    mark_processed(event_id)

    # Mock xreadgroup to return the message
    mock_redis.xreadgroup.return_value = [
        (STREAM_NAME, [("1234567890-0", {"envelope": envelope_json})])
    ]

    with patch("shared_py.events.handlers.get_redis", return_value=mock_redis):
        consumer_task = asyncio.create_task(
            start_consumer(redis_url="redis://localhost:6379/0", group="test-service")
        )

        # Wait a bit for processing
        await asyncio.sleep(0.3)

        await stop_consumer()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # Handler should NOT have been called
    assert handler_call_count == 0

    # Message should have been acked
    mock_redis.xack.assert_called()


# ═══════════════════════════════════════════════════════════════════════════
# Handler Failure and DLQ Tests
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_handler_failure_retries_and_dlqs(mock_redis):
    """Test that a failing handler is retried and eventually DLQ'd."""
    handler_call_count = 0

    @subscribe(event_type="ProductGraded")
    async def failing_handler(envelope: EventEnvelope):
        nonlocal handler_call_count
        handler_call_count += 1
        raise ValueError("Simulated handler failure")

    event_id = str(uuid.uuid4())
    test_envelope = EventEnvelope(
        event_id=event_id,
        event_type="ProductGraded",
        event_version="1.0",
        occurred_at=datetime.utcnow(),
        correlation_id="return-123",
        producer="grading",
        data={
            "return_id": "return-123",
            "grade_id": "grade-456",
            "product_id": "product-789",
            "grade": "A",
            "confidence": 0.95,
            "damage_summary": "Minor scratches",
            "defects": [],
        },
    )
    envelope_json = test_envelope.model_dump_json()
    message_id = "1234567890-0"

    # Mock xpending_range to simulate delivery count increasing
    delivery_count = 0

    async def mock_xpending_range(*args, **kwargs):
        nonlocal delivery_count
        delivery_count += 1
        return [{"times_delivered": delivery_count}]

    mock_redis.xpending_range.side_effect = mock_xpending_range

    # Mock xreadgroup to keep returning the same message
    mock_redis.xreadgroup.return_value = [
        (STREAM_NAME, [(message_id, {"envelope": envelope_json})])
    ]

    with patch("shared_py.events.handlers.get_redis", return_value=mock_redis):
        consumer_task = asyncio.create_task(
            start_consumer(redis_url="redis://localhost:6379/0", group="test-service")
        )

        # Wait for multiple retry attempts
        await asyncio.sleep(1.0)

        await stop_consumer()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # Handler should have been called multiple times (at least once)
    assert handler_call_count >= 1

    # After MAX_RETRIES, message should be moved to DLQ
    # Check that xadd was called with DLQ_STREAM
    dlq_calls = [
        call for call in mock_redis.xadd.call_args_list if call[0][0] == DLQ_STREAM
    ]
    assert len(dlq_calls) > 0


@pytest.mark.asyncio
async def test_multiple_handlers_same_event(mock_redis):
    """Test that multiple handlers for the same event type are all called."""
    handler1_called = False
    handler2_called = False

    @subscribe(event_type="ProductGraded")
    async def handler1(envelope: EventEnvelope):
        nonlocal handler1_called
        handler1_called = True

    @subscribe(event_type="ProductGraded")
    async def handler2(envelope: EventEnvelope):
        nonlocal handler2_called
        handler2_called = True

    test_envelope = EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type="ProductGraded",
        event_version="1.0",
        occurred_at=datetime.utcnow(),
        correlation_id="return-123",
        producer="grading",
        data={
            "return_id": "return-123",
            "grade_id": "grade-456",
            "product_id": "product-789",
            "grade": "A",
            "confidence": 0.95,
            "damage_summary": "Minor scratches",
            "defects": [],
        },
    )
    envelope_json = test_envelope.model_dump_json()

    mock_redis.xreadgroup.return_value = [
        (STREAM_NAME, [("1234567890-0", {"envelope": envelope_json})])
    ]

    with patch("shared_py.events.handlers.get_redis", return_value=mock_redis):
        consumer_task = asyncio.create_task(
            start_consumer(redis_url="redis://localhost:6379/0", group="test-service")
        )

        await asyncio.sleep(0.3)

        await stop_consumer()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # Both handlers should have been called
    assert handler1_called
    assert handler2_called


# ═══════════════════════════════════════════════════════════════════════════
# Payload Schema Tests
# ═══════════════════════════════════════════════════════════════════════════


def test_all_event_types_have_schemas():
    """Test that all 10 event types from architecture.md are registered."""
    expected_event_types = {
        "ReturnSubmitted",
        "ProductGraded",
        "LifecycleDecisionCreated",
        "PassportCreated",
        "HyperlocalMatchRequested",
        "MatchFound",
        "NoMatchFound",
        "ProductListed",
        "PurchaseCompleted",
        "SustainabilityUpdated",
    }
    assert set(EVENT_TYPE_TO_MODEL.keys()) == expected_event_types


def test_return_submitted_payload_validation():
    """Test ReturnSubmittedEventData validation."""
    valid_data = {
        "return_id": "return-123",
        "product_id": "product-456",
        "user_id": "user-789",
        "reason": "Defective",
        "media": ["s3://bucket/image1.jpg"],
    }
    payload = ReturnSubmittedEventData.model_validate(valid_data)
    assert payload.return_id == "return-123"
    assert payload.media == ["s3://bucket/image1.jpg"]


def test_product_graded_payload_validation():
    """Test ProductGradedEventData validation."""
    valid_data = {
        "return_id": "return-123",
        "grade_id": "grade-456",
        "product_id": "product-789",
        "grade": "B",
        "confidence": 0.87,
        "damage_summary": "Moderate wear",
        "defects": ["scratch", "dent"],
    }
    payload = ProductGradedEventData.model_validate(valid_data)
    assert payload.grade == "B"
    assert payload.confidence == 0.87
    assert len(payload.defects) == 2
