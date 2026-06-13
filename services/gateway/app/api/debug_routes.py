"""
Debug / observability endpoints for the API Gateway.

Owner: B (P0-B3) — added in coordination with A (gateway owner).

These endpoints are for development and demo use only.
They expose a read view of the event stream and DLQ directly from the Gateway,
so the frontend / team can inspect saga state without Redis CLI access.

⚠️  Do not expose these in production — guard with an env flag if hardening.

Routes
------
GET  /debug/events           — last N events from slmai:events
GET  /debug/events/dlq       — last N events from slmai:events:dlq
GET  /debug/events/stats     — counts per event_type
POST /debug/events/trigger   — publish a synthetic event (testing)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import shared constants — path is available because shared-py is installed
from shared_py.events.schemas import EVENT_TYPE_TO_MODEL

router = APIRouter(prefix="/debug/events", tags=["debug"])

# We can't import get_redis directly here (it needs a redis_url from settings).
# The endpoint creates its own connection using the REDIS_URL env var.
# This keeps the debug routes independent of the gateway's lifespan.

import os
import redis.asyncio as aioredis

STREAM_NAME = "slmai:events"
DLQ_STREAM = "slmai:events:dlq"


def _get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


def _parse_envelope(raw: dict[str, Any], msg_id: str) -> dict[str, Any]:
    """Parse a raw Redis stream message into a structured dict."""
    try:
        envelope = json.loads(raw.get("envelope", "{}"))
    except json.JSONDecodeError:
        return {"msg_id": msg_id, "parse_error": True, "raw": str(raw)}

    return {
        "msg_id": msg_id,
        "event_id": envelope.get("event_id"),
        "event_type": envelope.get("event_type"),
        "event_version": envelope.get("event_version"),
        "occurred_at": envelope.get("occurred_at"),
        "correlation_id": envelope.get("correlation_id"),
        "producer": envelope.get("producer"),
        "data": envelope.get("data", {}),
    }


# ── GET /debug/events ────────────────────────────────────────────────────────

@router.get("", summary="Last N events from the main stream")
async def get_events(
    count: int = Query(default=50, ge=1, le=500, description="Number of messages to return"),
    correlation_id: Optional[str] = Query(default=None, description="Filter by correlation_id prefix"),
    event_type: Optional[str] = Query(default=None, description="Filter by event_type"),
):
    """
    Read the last N messages from slmai:events.

    Useful for inspecting the saga state during development and demos.
    Results are ordered oldest → newest.
    """
    redis = aioredis.from_url(_get_redis_url(), encoding="utf-8", decode_responses=True)
    try:
        messages = await redis.xrevrange(STREAM_NAME, count=count)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")
    finally:
        await redis.aclose()

    events = [_parse_envelope(raw, msg_id) for msg_id, raw in reversed(messages)]

    # Apply filters
    if correlation_id:
        events = [e for e in events if (e.get("correlation_id") or "").startswith(correlation_id)]
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    return {
        "stream": STREAM_NAME,
        "count": len(events),
        "events": events,
    }


# ── GET /debug/events/dlq ────────────────────────────────────────────────────

@router.get("/dlq", summary="Last N events from the dead-letter queue")
async def get_dlq_events(
    count: int = Query(default=50, ge=1, le=500),
):
    """
    Read the last N messages from slmai:events:dlq.

    DLQ messages are events that failed handling after MAX_RETRIES attempts.
    Each affected Return will have status=FAILED.
    """
    redis = aioredis.from_url(_get_redis_url(), encoding="utf-8", decode_responses=True)
    try:
        messages = await redis.xrevrange(DLQ_STREAM, count=count)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")
    finally:
        await redis.aclose()

    events = [_parse_envelope(raw, msg_id) for msg_id, raw in reversed(messages)]

    return {
        "stream": DLQ_STREAM,
        "count": len(events),
        "events": events,
    }


# ── GET /debug/events/stats ──────────────────────────────────────────────────

@router.get("/stats", summary="Event counts per event_type")
async def get_event_stats():
    """
    Returns a summary of how many events of each type are in the stream and DLQ.
    Useful for verifying the saga is progressing correctly.
    """
    redis = aioredis.from_url(_get_redis_url(), encoding="utf-8", decode_responses=True)
    try:
        stream_msgs = await redis.xrange(STREAM_NAME, count=10000)
        dlq_msgs    = await redis.xrange(DLQ_STREAM, count=10000)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")
    finally:
        await redis.aclose()

    def _count_by_type(messages: list) -> dict[str, int]:
        counts: dict[str, int] = {}
        for _, raw in messages:
            try:
                et = json.loads(raw.get("envelope", "{}")).get("event_type", "unknown")
            except json.JSONDecodeError:
                et = "parse_error"
            counts[et] = counts.get(et, 0) + 1
        return counts

    return {
        "stream": {
            "name": STREAM_NAME,
            "total": len(stream_msgs),
            "by_type": _count_by_type(stream_msgs),
        },
        "dlq": {
            "name": DLQ_STREAM,
            "total": len(dlq_msgs),
            "by_type": _count_by_type(dlq_msgs),
        },
    }


# ── POST /debug/events/trigger ───────────────────────────────────────────────

class TriggerRequest(BaseModel):
    event_type: str
    correlation_id: Optional[str] = None
    data: dict[str, Any]


@router.post("/trigger", summary="Publish a synthetic event for testing")
async def trigger_event(body: TriggerRequest):
    """
    Publish a synthetic event directly to slmai:events.

    Validates the payload against the registered schema for the event_type.
    Useful for manually advancing a saga or smoke-testing a service handler.

    The producer is set to 'debug-trigger' so injected events are identifiable.
    """
    if body.event_type not in EVENT_TYPE_TO_MODEL:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown event_type '{body.event_type}'. "
                   f"Valid: {list(EVENT_TYPE_TO_MODEL.keys())}",
        )

    # Validate payload
    payload_model = EVENT_TYPE_TO_MODEL[body.event_type]
    try:
        validated = payload_model.model_validate(body.data).model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Payload validation failed: {e}")

    event_id = str(uuid.uuid4())
    correlation_id = body.correlation_id or body.data.get("return_id") or str(uuid.uuid4())

    envelope = {
        "event_id": event_id,
        "event_type": body.event_type,
        "event_version": "1.0",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "producer": "debug-trigger",
        "data": validated,
    }

    redis = aioredis.from_url(_get_redis_url(), encoding="utf-8", decode_responses=True)
    try:
        msg_id = await redis.xadd(STREAM_NAME, {"envelope": json.dumps(envelope)})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")
    finally:
        await redis.aclose()

    return {
        "published": True,
        "event_id": event_id,
        "event_type": body.event_type,
        "correlation_id": correlation_id,
        "stream_msg_id": msg_id,
        "stream": STREAM_NAME,
    }
