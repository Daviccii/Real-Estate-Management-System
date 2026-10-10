"""
Logging configuration for 12-Factor App compliance.

Factor 11: Logs as event streams
- All logs written to stdout (never to files in production)
- Structured JSON format for cloud log aggregation (Datadog, ELK, CloudWatch)
- Container orchestrators (Docker, Kubernetes) capture stdout
- No log rotation needed - that's the responsibility of the orchestration platform

Usage:
    from app.config.logging_config import setup_logging
    setup_logging()
"""
import logging
import sys
import json
from typing import Optional
from datetime import datetime
from app.utils.time import utc_now


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for cloud log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON."""
        log_data = {
            "timestamp": utc_now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields if provided
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        for key in ("method", "path", "client", "status", "duration_ms", "security"):
            value = getattr(record, key, None)
            if value is not None:
                log_data[key] = value

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Simple text formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as readable text."""
        timestamp = utc_now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_message = (
            f"{timestamp} | {record.levelname:8} | "
            f"{record.name}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )

        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    app_name: str = "real-estate-api",
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
) -> None:
    """
    Configure logging for 12-factor compliance.

    Args:
        log_level: logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: "json" for production or "text" for development
        app_name: application name for log identification
        log_to_file: additionally mirror logs to a rotated file (dev convenience;
            in production stdout is captured by the platform, which owns retention)
        log_file_path: target file for the rotated file handler

    12-Factor Compliance:
    - All logs to stdout (never files, in production)
    - JSON structured format for aggregation
    - Timestamped for troubleshooting
    """
    # Get or create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create stdout handler (12-factor: logs to stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level.upper())

    # Choose formatter based on environment
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Optional rotated mirror for non-container environments. Rotation keeps
    # retention bounded (5 x 10 MB); production log retention belongs to the
    # aggregation platform that captures stdout.
    if log_to_file:
        from logging.handlers import RotatingFileHandler

        if not log_file_path:
            raise ValueError("LOG_TO_FILE=true requires LOG_FILE_PATH")
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("sqlalchemy").setLevel("WARNING")
    logging.getLogger("sqlalchemy.pool").setLevel("WARNING")
    logging.getLogger("urllib3").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("INFO")

    # Log startup message
    logger = logging.getLogger(app_name)
    logger.info(
        f"Logging initialized",
        extra={
            "format": log_format,
            "level": log_level,
            "app": app_name,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
