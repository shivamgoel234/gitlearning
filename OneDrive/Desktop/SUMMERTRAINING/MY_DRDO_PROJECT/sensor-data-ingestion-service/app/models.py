"""
Pydantic models for Sensor Data Ingestion Service API.

Defines request/response schemas with validation rules.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class SensorReading(BaseModel):
    """
    Request model for sensor data ingestion.
    
    Validates all sensor readings against DRDO constraints.
    """
    equipment_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Equipment identifier (format: TYPE-LOCATION-NUMBER)"
    )
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=200.0,
        description="Temperature in Celsius"
    )
    vibration: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="Vibration level in mm/s"
    )
    pressure: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Pressure in bar"
    )
    humidity: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Humidity percentage"
    )
    voltage: Optional[float] = Field(
        None,
        ge=0.0,
        le=500.0,
        description="Voltage in V"
    )
    source: Optional[str] = Field(
        None,
        max_length=50,
        description="Data source identifier"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional notes"
    )
    
    @field_validator('equipment_id')
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        """Validate equipment ID format and normalize to uppercase."""
        v = v.upper()
        pattern = r'^[A-Z]+-[A-Z0-9]+-\d{3}$'
        if not re.match(pattern, v):
            raise ValueError(
                "Equipment ID must follow pattern: TYPE-LOCATION-NUMBER "
                "(e.g., RADAR-LOC-001)"
            )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "temperature": 85.5,
                "vibration": 0.45,
                "pressure": 3.2,
                "humidity": 65.0,
                "voltage": 220.0,
                "source": "iot-sensor-01",
                "notes": "Regular monitoring"
            }
        }


class SensorReadingResponse(BaseModel):
    """Response model for successful sensor data ingestion."""
    reading_id: str = Field(..., description="Unique identifier for the reading")
    equipment_id: str = Field(..., description="Equipment identifier")
    timestamp: datetime = Field(..., description="Timestamp of ingestion")
    status: str = Field(..., description="Ingestion status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reading_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "equipment_id": "RADAR-LOC-001",
                "timestamp": "2025-01-01T12:00:00Z",
                "status": "received"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(..., description="Current timestamp")
    database: Optional[str] = Field(None, description="Database connection status")
    redis: Optional[str] = Field(None, description="Redis connection status")


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="Error timestamp")
