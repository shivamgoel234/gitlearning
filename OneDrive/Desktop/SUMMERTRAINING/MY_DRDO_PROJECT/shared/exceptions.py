"""
Custom exceptions for DRDO Equipment Maintenance Prediction System.

Provides consistent error handling across all microservices.
"""

from typing import Optional, Dict, Any


class DRDOBaseException(Exception):
    """Base exception for all DRDO application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or "DRDO_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(DRDOBaseException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class DatabaseError(DRDOBaseException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class ServiceUnavailableError(DRDOBaseException):
    """Raised when a required service is unavailable."""
    
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Service unavailable: {service_name}"
        super().__init__(message, "SERVICE_UNAVAILABLE", details)


class ModelNotFoundError(DRDOBaseException):
    """Raised when ML model is not found or cannot be loaded."""
    
    def __init__(self, model_path: str):
        message = f"ML model not found at: {model_path}"
        super().__init__(message, "MODEL_NOT_FOUND", {"model_path": model_path})


class PredictionError(DRDOBaseException):
    """Raised when ML prediction fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PREDICTION_ERROR", details)


class EquipmentNotFoundError(DRDOBaseException):
    """Raised when equipment is not found in the system."""
    
    def __init__(self, equipment_id: str):
        message = f"Equipment not found: {equipment_id}"
        super().__init__(message, "EQUIPMENT_NOT_FOUND", {"equipment_id": equipment_id})


class AlertCreationError(DRDOBaseException):
    """Raised when alert creation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ALERT_CREATION_ERROR", details)


class NotificationError(DRDOBaseException):
    """Raised when sending notifications fails."""
    
    def __init__(self, notification_type: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to send {notification_type} notification"
        super().__init__(message, "NOTIFICATION_ERROR", details)


class ConfigurationError(DRDOBaseException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class AuthenticationError(DRDOBaseException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(DRDOBaseException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class RateLimitError(DRDOBaseException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None):
        message = "Rate limit exceeded"
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


class CircuitBreakerOpenError(DRDOBaseException):
    """Raised when circuit breaker is open (service protection)."""
    
    def __init__(self, service_name: str):
        message = f"Circuit breaker open for service: {service_name}"
        super().__init__(message, "CIRCUIT_BREAKER_OPEN", {"service": service_name})
