"""shared-py/config — base settings and structured logging for all services."""

from shared_py.config.logging import configure_logging, get_logger
from shared_py.config.settings import BaseServiceSettings

__all__ = ["BaseServiceSettings", "configure_logging", "get_logger"]
