"""
Logging configuration using structlog.
Follows Guardrail #11: Structured logging with JSON output.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from src.config import settings


def add_app_context(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to every log entry.
    Includes app name, version, and environment.
    """
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["environment"] = settings.environment
    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Uses structlog for structured JSON logging with:
    - Timestamps
    - Log levels
    - Application context (app name, version, environment)
    - Exception information
    - Request correlation IDs (when available)
    """

    # Determine log processors based on format
    if settings.log_format == "json":
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            add_app_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    else:
        # Human-readable format for development
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            add_app_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )


# Global logger instance
logger = structlog.get_logger()


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Utility function to log function calls with parameters.
    Useful for debugging and tracing.

    Example:
        log_function_call("synthesize_meeting", meeting_id=123, duration_sec=45)
    """
    logger.info(
        "function_called",
        function=func_name,
        **kwargs
    )


def log_performance(operation: str, duration_ms: float, **kwargs: Any) -> None:
    """
    Log performance metrics for operations.

    Example:
        start = time.time()
        # ... do work ...
        log_performance("database_query", (time.time() - start) * 1000, query_type="select")
    """
    logger.info(
        "performance_metric",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )
