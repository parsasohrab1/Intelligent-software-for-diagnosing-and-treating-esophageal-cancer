"""
Structured JSON logging configuration for INEsCape.

Provides configure_logging() which sets up the root logger to emit one
JSON object per line, and correlation_id_var, a ContextVar used by
CorrelationIdMiddleware to make the current request's correlation ID
available to every log record emitted while handling that request.
"""
import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

from app.core.config import settings

# Holds the correlation ID for the request currently being processed.
# Set/reset by CorrelationIdMiddleware for the lifetime of each request.
correlation_id_var: ContextVar = ContextVar("correlation_id", default=None)


class JSONLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = correlation_id_var.get()
        if correlation_id:
            payload["correlation_id"] = correlation_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger for structured JSON logging.

    Idempotent: safe to call multiple times (e.g. under test reloads)
    since it clears any handlers it previously attached.
    """
    root_logger = logging.getLogger()

    level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
    root_logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())

    root_logger.handlers = [handler]
