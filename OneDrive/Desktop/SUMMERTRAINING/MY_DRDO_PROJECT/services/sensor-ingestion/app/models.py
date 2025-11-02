"""
Pydantic models for request/response validation.

All API requests and responses use these models for type safety and validation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
import re


class SensorReading(BaseModel):
    """
    Request model for sensor data ingestion.
    
    Validates incoming sensor readings against defined constraints.
    """
    
    equipment_id: str = Field(
        ...,
        description="Unique equipment identifier (format: TYPE-LOCATION-NNN)",
        min_length=3,
        max_length=50,
        examples=["RADAR-LOC-001", "AIRCRAFT-BASE-042", "NAVAL-PORT-003"]
    )
    
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=200.0,
        description="Temperature reading in Celsius",
        examples=[85.5]
    )
    
    vibration: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="Vibration level in mm/s",
        examples=[0.45]
    )
    
    pressure: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Pressure reading in bar",
        examples=[3.2]
    )
    
    humidity: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Humidity percentage",
        examples=[65.0]
    )
    
    voltage: Optional[float] = Field(
        None,
        ge=0.0,
        le=500.0,
        description="Voltage reading in volts",
        examples=[220.0]
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the sensor reading (UTC)"
    )
    
    @field_validator('equipment_id')
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        """
        Validate equipment ID format: TYPE-LOCATION-NUMBER.
        
        Args:
            v: Equipment ID string
            
        Returns:
            Uppercase equipment ID
            
        Raises:
            ValueError: If format is invalid
        """
        if not v or len(v) < 3:
            raise ValueError('equipment_id must be at least 3 characters')
        
        # Convert to uppercase for consistency
        v = v.upper()
        
        # Validate format (TYPE-LOCATION-NNN)
        pattern = r'^[A-Z]+-[A-Z0-9]+-\d{3}$'
        if not re.match(pattern, v):
            raise ValueError(
                'equipment_id must follow format: TYPE-LOCATION-NNN '
                '(e.g., RADAR-LOC-001)'
            )
        
        return v
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """
        Additional temperature validation for extreme values.
        
        Args:
            v: Temperature value
            
        Returns:
            Validated temperature
        """
        if v < -40.0:
            # Log warning for extremely low temperatures
            pass  # Logger will be injected at service layer
        elif v > 150.0:
            # Log warning for extremely high temperatures
            pass
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "temperature": 85.5,
                "vibration": 0.45,
                "pressure": 3.2,
                "humidity": 65.0,
                "voltage": 220.0,
                "timestamp": "2025-11-01T18:30:00Z"
            }
        }
    )


class SensorReadingResponse(BaseModel):
    """Response model for successful sensor data ingestion."""
    
    reading_id: str = Field(
        ...,
        description="Unique identifier for this reading"
    )
    equipment_id: str = Field(
        ...,
        description="Equipment identifier"
    )
    status: str = Field(
        default="received",
        description="Ingestion status"
    )
    timestamp: datetime = Field(
        ...,
        description="Reading timestamp"
    )
    message: str = Field(
        default="Sensor data ingested successfully",
        description="Status message"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reading_id": "123e4567-e89b-12d3-a456-426614174000",
                "equipment_id": "RADAR-LOC-001",
                "status": "received",
                "timestamp": "2025-11-01T18:30:00Z",
                "message": "Sensor data ingested successfully"
            }
        }
    )


class SensorReadingBatch(BaseModel):
    """Request model for batch sensor data ingestion."""
    
    readings: list[SensorReading] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of sensor readings (max 100 per batch)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "readings": [
                    {
                        "equipment_id": "RADAR-LOC-001",
                        "temperature": 85.5,
                        "vibration": 0.45,
                        "pressure": 3.2,
                        "humidity": 65.0,
                        "voltage": 220.0
                    },
                    {
                        "equipment_id": "RADAR-LOC-002",
                        "temperature": 78.2,
                        "vibration": 0.38,
                        "pressure": 3.0,
                        "humidity": 62.0,
                        "voltage": 215.0
                    }
                ]
            }
        }
    )


class SensorReadingBatchResponse(BaseModel):
    """Response model for batch sensor data ingestion."""
    
    total: int = Field(
        ...,
        description="Total number of readings in batch"
    )
    successful: int = Field(
        ...,
        description="Number of successfully ingested readings"
    )
    failed: int = Field(
        ...,
        description="Number of failed readings"
    )
    reading_ids: list[str] = Field(
        ...,
        description="List of reading IDs for successful ingestions"
    )
    errors: list[dict] = Field(
        default_factory=list,
        description="List of errors for failed readings"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "successful": 2,
                "failed": 0,
                "reading_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001"
                ],
                "errors": []
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(
        ...,
        description="Error type/category"
    )
    detail: str = Field(
        ...,
        description="Detailed error message"
    )
    status_code: int = Field(
        ...,
        description="HTTP status code"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request correlation ID for tracing"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "detail": "temperature must be between -50.0 and 200.0",
                "status_code": 422,
                "timestamp": "2025-11-01T18:30:00Z",
                "request_id": "req-123e4567"
            }
        }
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    service: str = Field(
        ...,
        description="Service name"
    )
    status: str = Field(
        ...,
        description="Overall service status (healthy/unhealthy)"
    )
    version: str = Field(
        ...,
        description="Service version"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    database: str = Field(
        ...,
        description="Database connection status"
    )
    redis: str = Field(
        ...,
        description="Redis connection status"
    )
    uptime_seconds: Optional[float] = Field(
        None,
        description="Service uptime in seconds"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "sensor-ingestion-service",
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-01T18:30:00Z",
                "database": "connected",
                "redis": "connected",
                "uptime_seconds": 3600.5
            }
        }
    )


class ReadinessCheckResponse(BaseModel):
    """Readiness check response model for Kubernetes."""
    
    ready: bool = Field(
        ...,
        description="Service readiness status"
    )
    checks: dict[str, str] = Field(
        ...,
        description="Individual component readiness checks"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ready": True,
                "checks": {
                    "database": "ready",
                    "redis": "ready"
                }
            }
        }
    )


class LatestReadingsResponse(BaseModel):
    """Response model for latest readings query."""
    
    equipment_id: str = Field(
        ...,
        description="Equipment identifier"
    )
    count: int = Field(
        ...,
        description="Number of readings returned"
    )
    readings: list[dict] = Field(
        ...,
        description="List of sensor readings"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "count": 5,
                "readings": [
                    {
                        "reading_id": "123e4567-e89b-12d3-a456-426614174000",
                        "temperature": 85.5,
                        "vibration": 0.45,
                        "pressure": 3.2,
                        "timestamp": "2025-11-01T18:30:00Z"
                    }
                ]
            }
        }
    )
