"""
Event-saga observability tail script — implemented in P0-B3 (Owner: B).
Tails slmai:events stream and the DLQ (slmai:events:dlq).
Also supports manual event trigger/replay.

Usage:
    python scripts/events_tail.py [--dlq] [--replay <event_id>]
"""

# TODO: P0-B3 — event tail + replay
