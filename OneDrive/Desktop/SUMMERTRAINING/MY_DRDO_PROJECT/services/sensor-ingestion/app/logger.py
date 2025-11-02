"""
Structured JSON logging configuration.

Implements JSON-formatted logging for production observability,
following 12-factor app principles (logs to stdout).
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

from .config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Outputs logs in JSON format for easy parsing by log aggregation systems
    like ELK, Splunk, or CloudWatch.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "environment": settings.ENVIRONMENT,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "equipment_id"):
            log_data["equipment_id"] = record.equipment_id
        
        if hasattr(record, "reading_id"):
            log_data["reading_id"] = record.reading_id
        
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.
    
    Used when LOG_FORMAT is set to "text".
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as human-readable text.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Base format
        message = (
            f"[{timestamp}] "
            f"{record.levelname:8s} "
            f"{record.name:25s} "
            f"| {record.getMessage()}"
        )
        
        # Add request ID if present
        if hasattr(record, "request_id"):
            message += f" | req_id={record.request_id}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging() -> None:
    """
    Configure application logging.
    
    Sets up structured JSON logging or text logging based on configuration.
    Follows 12-factor app principle: logs to stdout only.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Set formatter based on config
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)
    
    # Optional: Add file handler (not recommended for production)
    if settings.LOG_TO_FILE:
        log_file = Path(settings.LOG_FILE_PATH)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info(
        f"Logging configured: level={settings.LOG_LEVEL}, format={settings.LOG_FORMAT}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to logs.
    
    Usage:
        logger = LoggerAdapter(get_logger(__name__), {"request_id": "req-123"})
        logger.info("Processing request")  # Includes request_id in log
    """
    
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """
        Process log message to add extra context.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (message, kwargs) with extra fields
        """
        # Add extra context from adapter
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        
        return msg, kwargs
