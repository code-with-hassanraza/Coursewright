import logging
import sys
from typing import Any, Dict

from app.core.config import settings


class CourseWrightFormatter(logging.Formatter):
    """
    Custom formatter that adds context to log records.
    Outputs clean single-line logs in development,
    structured logs in production.
    """

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        if settings.ENVIRONMENT == "production":
            return self._format_production(record)
        return self._format_development(record)

    def _format_development(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        level = f"{color}{record.levelname:<8}{reset}"
        location = f"{record.name}:{record.lineno}"
        return f"{self.formatTime(record, '%H:%M:%S')} | {level} | {location} | {record.getMessage()}"

    def _format_production(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        import json
        return json.dumps(log_obj)


def setup_logging() -> None:
    """
    Call this once in main.py on startup.
    Configures root logger and suppresses noisy third-party loggers.
    """
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CourseWrightFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Use this everywhere in the codebase instead of logging.getLogger directly.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("User registered", extra={"user_id": str(user.id)})
    """
    return logging.getLogger(name)