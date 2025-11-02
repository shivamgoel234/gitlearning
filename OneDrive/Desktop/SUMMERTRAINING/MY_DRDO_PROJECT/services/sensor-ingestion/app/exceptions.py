"""
Custom exception classes for the sensor ingestion service.

Provides specific exception types for different error scenarios.
"""

from typing import Optional


class SensorIngestionException(Exception):
    """Base exception for sensor ingestion service."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SensorIngestionException):
    """Raised when sensor data validation fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=422, details=details)


class DatabaseError(SensorIngestionException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class RedisError(SensorIngestionException):
    """Raised when Redis operations fail."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class EquipmentNotFoundError(SensorIngestionException):
    """Raised when equipment ID is not found."""
    
    def __init__(self, equipment_id: str):
        message = f"Equipment not found: {equipment_id}"
        super().__init__(message, status_code=404, details={"equipment_id": equipment_id})


class SensorAnomalyError(SensorIngestionException):
    """Raised when sensor readings indicate anomalous behavior."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=422, details=details)


class RateLimitExceededError(SensorIngestionException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message,
            status_code=429,
            details={"retry_after_seconds": retry_after}
        )
