"""
Shared Pydantic models for DRDO Equipment Maintenance Prediction System.

Common request/response models used across multiple microservices.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ServiceStatus(str, Enum):
    """Service health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SeverityLevel(str, Enum):
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MaintenanceStatus(str, Enum):
    """Maintenance schedule status."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class HealthCheckResponse(BaseModel):
    """
    Standard health check response for all services.
    
    Used by Kubernetes/Docker for liveness and readiness probes.
    """
    status: ServiceStatus = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    dependencies: Optional[Dict[str, str]] = Field(
        None,
        description="Status of dependent services (database, redis, etc.)"
    )
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "sensor-ingestion",
                "version": "1.0.0",
                "timestamp": "2025-01-01T12:00:00Z",
                "dependencies": {
                    "database": "connected",
                    "redis": "connected"
                },
                "uptime_seconds": 3600.5
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response for all API endpoints.
    
    Provides consistent error format across all microservices.
    """
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Invalid equipment ID format",
                "details": {
                    "field": "equipment_id",
                    "constraint": "Must match pattern TYPE-LOCATION-NUMBER"
                },
                "timestamp": "2025-01-01T12:00:00Z",
                "correlation_id": "req-abc-123"
            }
        }


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    items: List[Any] = Field(..., description="List of items for current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class EquipmentBase(BaseModel):
    """Base equipment information shared across services."""
    equipment_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Equipment identifier (format: TYPE-LOCATION-NUMBER)"
    )
    
    @field_validator('equipment_id')
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        """Validate and normalize equipment ID."""
        import re
        v = v.upper()
        pattern = r'^[A-Z]+-[A-Z0-9]+-\d{3}$'
        if not re.match(pattern, v):
            raise ValueError(
                "Equipment ID must follow pattern: TYPE-LOCATION-NUMBER "
                "(e.g., RADAR-LOC-001)"
            )
        return v


class SensorReadingBase(BaseModel):
    """Base sensor reading data."""
    temperature: float = Field(..., ge=-50.0, le=200.0, description="Temperature in °C")
    vibration: float = Field(..., ge=0.0, le=2.0, description="Vibration in mm/s")
    pressure: float = Field(..., ge=0.0, le=10.0, description="Pressure in bar")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Humidity in %")
    voltage: Optional[float] = Field(None, ge=0.0, le=500.0, description="Voltage in V")


class PredictionBase(BaseModel):
    """Base prediction data."""
    failure_probability: float = Field(..., ge=0.0, le=1.0, description="Failure probability")
    severity: SeverityLevel = Field(..., description="Severity classification")
    health_score: float = Field(..., ge=0.0, le=100.0, description="Health score (0-100)")
    days_until_failure: int = Field(..., ge=0, description="Estimated days until failure")
    confidence: str = Field(..., description="Prediction confidence level")


class AlertBase(BaseModel):
    """Base alert information."""
    severity: SeverityLevel = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    acknowledged: bool = Field(default=False, description="Acknowledgment status")


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": "123", "status": "processed"},
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }


class MetricsResponse(BaseModel):
    """Standard metrics response for Prometheus."""
    metric_name: str = Field(..., description="Metric identifier")
    value: float = Field(..., description="Metric value")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchOperationResponse(BaseModel):
    """Response for batch operations."""
    total: int = Field(..., description="Total items in batch")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error details")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100


class ServiceInfo(BaseModel):
    """Service information for discovery and documentation."""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: str = Field(..., description="Service description")
    endpoints: List[str] = Field(..., description="Available API endpoints")
    dependencies: List[str] = Field(..., description="Service dependencies")
    documentation_url: Optional[str] = Field(None, description="API documentation URL")
