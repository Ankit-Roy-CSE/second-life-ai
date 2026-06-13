"""
Structured JSON logging for all Amazon Second Life AI services.

Usage:
    from shared_py.config import configure_logging, get_logger

    configure_logging(service_name="grading", level="INFO")
    logger = get_logger(__name__)

    logger.info("product graded", extra={"correlation_id": "...", "grade": "A"})

Every log record emitted through this logger is a single-line JSON object with:
    service, level, message, timestamp (ISO-8601 UTC), and any extra fields.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service = service_name

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        # Base fields always present
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self._service,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Propagate correlation_id and event_id when callers add them via extra={}
        for key in ("correlation_id", "event_id", "user_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        # Include exception info when present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


_configured_service: str = "service"


def configure_logging(service_name: str, level: str = "INFO") -> None:
    """
    Configure root logger to emit structured JSON to stdout.
    Call once at application startup (inside lifespan or before create_app).
    """
    global _configured_service  # noqa: PLW0603
    _configured_service = service_name

    formatter = _JsonFormatter(service_name)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a standard Logger. Use module __name__ as the name:

        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
