"""
Pydantic models for ML Prediction Service API.

Defines request/response schemas with validation rules.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class PredictionRequest(BaseModel):
    """
    Request model for failure prediction.
    
    Accepts sensor readings and returns failure probability.
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
        0.0,
        ge=0.0,
        le=100.0,
        description="Humidity percentage"
    )
    voltage: Optional[float] = Field(
        0.0,
        ge=0.0,
        le=500.0,
        description="Voltage in V"
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
                "voltage": 220.0
            }
        }


class PredictionResponse(BaseModel):
    """Response model for failure prediction."""
    prediction_id: str = Field(..., description="Unique prediction identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    failure_probability: float = Field(..., description="Failure probability (0-1)")
    severity: str = Field(..., description="Severity level (CRITICAL/HIGH/MEDIUM/LOW)")
    health_score: float = Field(..., description="Equipment health score (0-100)")
    days_until_failure: int = Field(..., description="Estimated days until failure")
    confidence: str = Field(..., description="Prediction confidence (high/medium/low)")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction_id": "pred-123-456",
                "equipment_id": "RADAR-LOC-001",
                "failure_probability": 0.75,
                "severity": "HIGH",
                "health_score": 35.5,
                "days_until_failure": 15,
                "confidence": "high",
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }


class HealthScoreRequest(BaseModel):
    """Request model for equipment health score calculation."""
    equipment_id: str = Field(..., description="Equipment identifier")
    
    @field_validator('equipment_id')
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        """Validate equipment ID format."""
        return v.upper()


class HealthScoreResponse(BaseModel):
    """Response model for health score calculation."""
    equipment_id: str = Field(..., description="Equipment identifier")
    health_score: float = Field(..., description="Current health score (0-100)")
    status: str = Field(..., description="Health status")
    last_prediction: Optional[datetime] = Field(None, description="Last prediction timestamp")
    trend: Optional[str] = Field(None, description="Health trend (improving/stable/declining)")


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(..., description="Current timestamp")
    database: Optional[str] = Field(None, description="Database connection status")
    redis: Optional[str] = Field(None, description="Redis connection status")
    model_loaded: Optional[bool] = Field(None, description="ML model loaded status")


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="Error timestamp")
