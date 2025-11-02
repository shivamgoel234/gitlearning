"""
Structured logging configuration for DRDO Equipment Maintenance Prediction System.

Provides consistent logging across all microservices with:
- JSON-formatted logs for easy parsing
- Correlation IDs for request tracing
- Contextual information (service name, timestamp, etc.)
- Log level configuration via environment variables
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
import traceback

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Outputs logs in JSON format with standardized fields for easy parsing
    by log aggregation systems (ELK, Splunk, etc.).
    """
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data["extra"] = record.extra_fields
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, default=str)


class ContextLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log records.
    
    Allows adding extra fields to all log messages from this logger instance.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Add extra context to log records."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        # Merge adapter context with log-specific extra fields
        extra_fields = {**self.extra, **kwargs["extra"]}
        kwargs["extra"]["extra_fields"] = extra_fields
        
        return msg, kwargs


def setup_logger(
    service_name: str,
    log_level: str = "INFO",
    json_format: bool = True
) -> logging.Logger:
    """
    Setup and configure logger for a microservice.
    
    Args:
        service_name: Name of the microservice (e.g., "sensor-ingestion")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting (True for production)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger("sensor-ingestion", "INFO")
        >>> logger.info("Service started", extra={"port": 8001})
    """
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set formatter
    if json_format:
        formatter = JSONFormatter(service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str, **context: Any) -> ContextLogger:
    """
    Get a logger with additional context.
    
    Args:
        name: Logger name (usually __name__)
        **context: Additional context to add to all log messages
    
    Returns:
        ContextLogger with extra context
    
    Example:
        >>> logger = get_logger(__name__, equipment_id="RADAR-001")
        >>> logger.info("Processing sensor data")  # Includes equipment_id in log
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for request tracing.
    
    Should be called at the start of each request to enable
    tracing logs across services.
    
    Args:
        correlation_id: Unique identifier for request tracking
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear correlation ID (usually at end of request)."""
    correlation_id_var.set(None)


# Example usage and testing
if __name__ == "__main__":
    # Setup logger
    logger = setup_logger("test-service", "INFO", json_format=True)
    
    # Test basic logging
    logger.info("Service started successfully")
    logger.warning("This is a warning message")
    
    # Test with correlation ID
    set_correlation_id("req-123-456")
    logger.info("Processing request with correlation ID")
    clear_correlation_id()
    
    # Test with extra context
    ctx_logger = get_logger(__name__, equipment_id="RADAR-001")
    ctx_logger.info("Equipment data received")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except ValueError:
        logger.exception("An error occurred")
