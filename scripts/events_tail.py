"""
Event-saga observability tool for Amazon Second Life AI.

Owner: B (P0-B3)

Three capabilities:
  1. tail     — live-stream slmai:events (and optionally the DLQ) to stdout
  2. dump     — print all existing messages in the stream / DLQ
  3. trigger  — publish a synthetic event to slmai:events for manual testing
  4. replay   — re-publish a DLQ message back to slmai:events for recovery

Usage
-----
    # Tail the live event stream (Ctrl-C to stop)
    python scripts/events_tail.py tail

    # Tail including the DLQ
    python scripts/events_tail.py tail --dlq

    # Tail only a specific correlation_id (return/saga ID)
    python scripts/events_tail.py tail --correlation-id <uuid>

    # Dump the last N messages from the stream
    python scripts/events_tail.py dump --count 50

    # Dump the DLQ
    python scripts/events_tail.py dump --dlq

    # Trigger a synthetic ReturnSubmitted event (for smoke testing)
    python scripts/events_tail.py trigger ReturnSubmitted \\
        --data '{"return_id":"uuid","product_id":"uuid","user_id":"uuid","reason":"Test","media":[]}'

    # Trigger using the golden-path demo return
    python scripts/events_tail.py trigger ReturnSubmitted --golden-path

    # Replay a message from the DLQ back to the main stream
    python scripts/events_tail.py replay <dlq_message_id>

Environment
-----------
    REDIS_URL — defaults to redis://localhost:6379/0
"""

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Bootstrap shared_py path ────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "shared-py"))

try:
    import redis.asyncio as aioredis
except ImportError:
    print("[events_tail] Missing dependency: redis")
    print("Run: pip install redis")
    sys.exit(1)

from shared_py.events.schemas import EVENT_TYPE_TO_MODEL

# ── Constants ───────────────────────────────────────────────────────────────
STREAM_NAME = "slmai:events"
DLQ_STREAM = "slmai:events:dlq"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Golden-path trigger data (matches seed_min.py UUIDs)
_GOLDEN_RETURN_ID  = "8a4e9c5b-f2d1-5e6a-9b3c-7d8e0f1a2b3c"  # det uuid "return.golden"
_GOLDEN_PRODUCT_ID = "2f7a1d3e-c4b5-5a6e-8d9c-0e1f2a3b4c5d"  # det uuid "product.headphones"
_GOLDEN_USER_ID    = "1a2b3c4d-e5f6-5a7b-8c9d-0e1f2a3b4c5d"  # det uuid "user.returner"

try:
    from shared_py.ai.client import (
        GOLDEN_PATH_MEDIA_KEY,
        GOLDEN_PATH_REASON,
    )
except ImportError:
    GOLDEN_PATH_MEDIA_KEY = "products/golden-path/demo-headphones-001.jpg"
    GOLDEN_PATH_REASON = "Item not as expected"

GOLDEN_PATH_TRIGGER_DATA: dict[str, Any] = {
    "ReturnSubmitted": {
        "return_id": _GOLDEN_RETURN_ID,
        "product_id": _GOLDEN_PRODUCT_ID,
        "user_id": _GOLDEN_USER_ID,
        "reason": GOLDEN_PATH_REASON,
        "media": [GOLDEN_PATH_MEDIA_KEY],
    },
}

# ── ANSI colours (disabled on non-TTY) ──────────────────────────────────────
_USE_COLOR = sys.stdout.isatty()

_COLORS = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "cyan":    "\033[36m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "red":     "\033[31m",
    "magenta": "\033[35m",
    "grey":    "\033[90m",
}

EVENT_COLORS: dict[str, str] = {
    "ReturnSubmitted":          "cyan",
    "ProductGraded":            "green",
    "LifecycleDecisionCreated": "green",
    "PassportCreated":          "magenta",
    "HyperlocalMatchRequested": "magenta",
    "MatchFound":               "yellow",
    "NoMatchFound":             "yellow",
    "ProductListed":            "yellow",
    "PurchaseCompleted":        "bold",
    "SustainabilityUpdated":    "cyan",
}


def _c(color: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


# ── Formatting ───────────────────────────────────────────────────────────────

def _format_envelope(raw: dict[str, Any], msg_id: str, source: str = "stream") -> str:
    """Render an event envelope as a readable one-line summary."""
    try:
        envelope = json.loads(raw.get("envelope", "{}"))
    except json.JSONDecodeError:
        return f"  [PARSE ERROR] raw={raw}"

    event_type  = envelope.get("event_type", "Unknown")
    corr_id     = envelope.get("correlation_id", "—")[:8]
    occurred_at = envelope.get("occurred_at", "—")[:19].replace("T", " ")
    producer    = envelope.get("producer", "—")
    event_id    = envelope.get("event_id", "—")[:8]

    color  = "red" if source == "dlq" else EVENT_COLORS.get(event_type, "reset")
    prefix = _c("red", "[DLQ]") if source == "dlq" else _c("grey", "[stream]")
    etype  = _c(color, f"{event_type:<35}")

    data   = envelope.get("data", {})
    data_preview = ", ".join(f"{k}={str(v)[:20]}" for k, v in list(data.items())[:3])

    return (
        f"{prefix} {_c('grey', occurred_at)}  "
        f"{etype}  "
        f"corr={_c('cyan', corr_id)}...  "
        f"from={_c('grey', producer):<15}  "
        f"evt_id={_c('grey', event_id)}...  "
        f"msg_id={_c('grey', msg_id)}  "
        f"{_c('grey', data_preview)}"
    )


def _print_header() -> None:
    print(_c("bold", "\n─── Amazon Second Life AI — Event Stream ───"))
    print(_c("grey", f"  Stream : {STREAM_NAME}"))
    print(_c("grey", f"  DLQ    : {DLQ_STREAM}"))
    print(_c("grey", f"  Redis  : {REDIS_URL}"))
    print(_c("bold", "─" * 50))


# ── Commands ─────────────────────────────────────────────────────────────────

async def cmd_tail(args: argparse.Namespace) -> None:
    """Tail the event stream live."""
    _print_header()
    print(_c("green", "Tailing live events... (Ctrl-C to stop)\n"))

    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    # Start reading from the latest message ($ = only new events)
    last_stream_id = "$"
    last_dlq_id    = "$"

    filter_corr = args.correlation_id if hasattr(args, "correlation_id") else None
    show_dlq    = args.dlq if hasattr(args, "dlq") else False

    try:
        while True:
            streams_to_read: dict[str, str] = {STREAM_NAME: last_stream_id}
            if show_dlq:
                streams_to_read[DLQ_STREAM] = last_dlq_id

            messages = await redis.xread(streams_to_read, block=1000, count=50)

            for stream_key, entries in (messages or []):
                source = "dlq" if stream_key == DLQ_STREAM else "stream"
                for msg_id, raw in entries:
                    try:
                        envelope = json.loads(raw.get("envelope", "{}"))
                    except json.JSONDecodeError:
                        envelope = {}

                    corr_id = envelope.get("correlation_id", "")
                    if filter_corr and not corr_id.startswith(filter_corr):
                        continue  # skip non-matching correlations

                    print(_format_envelope(raw, msg_id, source=source))

                    if stream_key == STREAM_NAME:
                        last_stream_id = msg_id
                    else:
                        last_dlq_id = msg_id

    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        await redis.aclose()
        print(_c("grey", "\n[tail] Stopped."))


async def cmd_dump(args: argparse.Namespace) -> None:
    """Dump existing messages from the stream or DLQ."""
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    count = args.count if hasattr(args, "count") else 100
    show_dlq = args.dlq if hasattr(args, "dlq") else False

    targets = []
    if show_dlq:
        targets.append((DLQ_STREAM, "dlq"))
    else:
        targets.append((STREAM_NAME, "stream"))

    try:
        for stream_key, source in targets:
            print(_c("bold", f"\n─── {stream_key} (last {count}) ───"))
            try:
                messages = await redis.xrevrange(stream_key, count=count)
            except Exception as e:
                print(f"  [dump] Cannot read {stream_key}: {e}")
                continue

            if not messages:
                print(_c("grey", "  (empty)"))
                continue

            # Reverse to show oldest-first
            for msg_id, raw in reversed(messages):
                print(_format_envelope(raw, msg_id, source=source))

            print(_c("grey", f"\n  {len(messages)} message(s) shown."))
    finally:
        await redis.aclose()


async def cmd_trigger(args: argparse.Namespace) -> None:
    """Publish a synthetic event to the stream."""
    event_type = args.event_type

    if event_type not in EVENT_TYPE_TO_MODEL:
        print(f"[trigger] Unknown event_type '{event_type}'.")
        print(f"  Valid types: {', '.join(EVENT_TYPE_TO_MODEL.keys())}")
        sys.exit(1)

    # Resolve payload
    use_golden = hasattr(args, "golden_path") and args.golden_path
    if use_golden:
        if event_type not in GOLDEN_PATH_TRIGGER_DATA:
            print(f"[trigger] No golden-path data for '{event_type}'. Use --data instead.")
            sys.exit(1)
        raw_data = GOLDEN_PATH_TRIGGER_DATA[event_type]
        print(_c("yellow", f"[trigger] Using golden-path data for {event_type}"))
    elif hasattr(args, "data") and args.data:
        try:
            raw_data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"[trigger] Invalid JSON in --data: {e}")
            sys.exit(1)
    else:
        print("[trigger] Provide --data <json> or --golden-path")
        sys.exit(1)

    # Validate against schema
    payload_model = EVENT_TYPE_TO_MODEL[event_type]
    try:
        validated = payload_model.model_validate(raw_data).model_dump(mode="json")
    except Exception as e:
        print(f"[trigger] Payload validation failed: {e}")
        sys.exit(1)

    # Build envelope
    correlation_id = raw_data.get("return_id") or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    envelope = {
        "event_id": event_id,
        "event_type": event_type,
        "event_version": "1.0",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "producer": "events_tail_trigger",
        "data": validated,
    }

    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        msg_id = await redis.xadd(STREAM_NAME, {"envelope": json.dumps(envelope)})
        print(_c("green", f"[trigger] Published {event_type}"))
        print(f"  event_id       = {event_id}")
        print(f"  correlation_id = {correlation_id}")
        print(f"  stream_msg_id  = {msg_id}")
        print(f"  stream         = {STREAM_NAME}")
    except Exception as e:
        print(_c("red", f"[trigger] Failed: {e}"))
        sys.exit(1)
    finally:
        await redis.aclose()


async def cmd_replay(args: argparse.Namespace) -> None:
    """Re-publish a DLQ message back to the main stream for recovery."""
    dlq_msg_id = args.message_id

    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        # Read the specific message from the DLQ
        messages = await redis.xrange(DLQ_STREAM, min=dlq_msg_id, max=dlq_msg_id, count=1)

        if not messages:
            print(f"[replay] Message '{dlq_msg_id}' not found in {DLQ_STREAM}")
            sys.exit(1)

        msg_id, raw = messages[0]
        print(f"[replay] Found DLQ message: {msg_id}")
        print(_format_envelope(raw, msg_id, source="dlq"))

        # Confirm
        if not (hasattr(args, "yes") and args.yes):
            confirm = input(
                _c("yellow", "\nRe-publish this message to the main stream? [y/N] ")
            ).strip().lower()
            if confirm != "y":
                print("[replay] Aborted.")
                await redis.aclose()
                return

        # Re-publish to main stream
        new_msg_id = await redis.xadd(STREAM_NAME, raw)
        print(_c("green", f"[replay] Re-published to {STREAM_NAME}"))
        print(f"  new_stream_msg_id = {new_msg_id}")
        print(f"  original_dlq_id   = {dlq_msg_id}")

    except Exception as e:
        print(_c("red", f"[replay] Failed: {e}"))
        sys.exit(1)
    finally:
        await redis.aclose()


async def cmd_stats(args: argparse.Namespace) -> None:
    """Print stream statistics — message counts per event_type."""
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        print(_c("bold", "\n─── Event Stream Stats ───"))

        for stream_key, label in [(STREAM_NAME, "Main"), (DLQ_STREAM, "DLQ")]:
            try:
                all_msgs = await redis.xrange(stream_key, count=10000)
            except Exception:
                all_msgs = []

            counts: dict[str, int] = {}
            for _, raw in all_msgs:
                try:
                    envelope = json.loads(raw.get("envelope", "{}"))
                    et = envelope.get("event_type", "Unknown")
                    counts[et] = counts.get(et, 0) + 1
                except json.JSONDecodeError:
                    counts["PARSE_ERROR"] = counts.get("PARSE_ERROR", 0) + 1

            total = sum(counts.values())
            color = "red" if label == "DLQ" else "green"
            print(f"\n  {_c(color, label)} stream ({STREAM_NAME if label == 'Main' else DLQ_STREAM}): {total} messages")
            if counts:
                for et in sorted(counts, key=lambda k: -counts[k]):
                    bar = "█" * min(counts[et], 40)
                    print(f"    {et:<35} {counts[et]:>4}  {_c('grey', bar)}")
            else:
                print(_c("grey", "    (empty)"))
    finally:
        await redis.aclose()


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="events_tail",
        description="Amazon Second Life AI — event stream observability tool",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # tail
    p_tail = sub.add_parser("tail", help="Live-tail the event stream")
    p_tail.add_argument("--dlq", action="store_true", help="Also tail the DLQ stream")
    p_tail.add_argument(
        "--correlation-id", metavar="UUID",
        help="Filter to events matching this correlation_id prefix"
    )

    # dump
    p_dump = sub.add_parser("dump", help="Dump existing stream messages")
    p_dump.add_argument("--dlq", action="store_true", help="Dump the DLQ instead")
    p_dump.add_argument("--count", type=int, default=100, help="Number of messages (default 100)")

    # trigger
    p_trigger = sub.add_parser("trigger", help="Publish a synthetic event for testing")
    p_trigger.add_argument("event_type", help=f"Event type. One of: {', '.join(EVENT_TYPE_TO_MODEL.keys())}")
    p_trigger.add_argument("--data", metavar="JSON", help="JSON payload string")
    p_trigger.add_argument("--golden-path", action="store_true", help="Use golden-path demo data")

    # replay
    p_replay = sub.add_parser("replay", help="Re-publish a DLQ message to the main stream")
    p_replay.add_argument("message_id", help="DLQ message ID to replay (from dump --dlq)")
    p_replay.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # stats
    sub.add_parser("stats", help="Print event counts per event_type")

    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Test Redis connectivity before running any command
    try:
        redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await redis.ping()
        await redis.aclose()
    except Exception as e:
        print(_c("red", f"[events_tail] Cannot connect to Redis at {REDIS_URL}: {e}"))
        print("  Is Redis running? Try: docker compose up redis")
        sys.exit(1)

    dispatch = {
        "tail":    cmd_tail,
        "dump":    cmd_dump,
        "trigger": cmd_trigger,
        "replay":  cmd_replay,
        "stats":   cmd_stats,
    }
    await dispatch[args.command](args)


if __name__ == "__main__":
    asyncio.run(main())
