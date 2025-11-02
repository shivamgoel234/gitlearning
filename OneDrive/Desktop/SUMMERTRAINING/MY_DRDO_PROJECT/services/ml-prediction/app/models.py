"""
Pydantic models for ML prediction service.

Defines request and response schemas for the API.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class SensorData(BaseModel):
    """
    Request model for equipment sensor data.
    
    Contains sensor readings for failure prediction.
    """
    
    equipment_id: str = Field(
        ...,
        description="Unique equipment identifier",
        min_length=3,
        max_length=50,
        examples=["RADAR-LOC-001"]
    )
    
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=200.0,
        description="Temperature in Celsius",
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
        description="Pressure in bar",
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
        description="Voltage in volts",
        examples=[220.0]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "temperature": 85.5,
                "vibration": 0.45,
                "pressure": 3.2,
                "humidity": 65.0,
                "voltage": 220.0
            }
        }
    )


class PredictionResponse(BaseModel):
    """Response model for failure prediction."""
    
    equipment_id: str = Field(
        ...,
        description="Equipment identifier"
    )
    
    prediction: int = Field(
        ...,
        description="Binary prediction: 1 = failure likely, 0 = normal",
        ge=0,
        le=1
    )
    
    failure_probability: float = Field(
        ...,
        description="Probability of failure (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    severity: str = Field(
        ...,
        description="Failure severity level",
        examples=["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    )
    
    days_until_failure: int = Field(
        ...,
        description="Estimated days until failure",
        ge=0
    )
    
    confidence: str = Field(
        ...,
        description="Prediction confidence level",
        examples=["high", "medium", "low"]
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Prediction timestamp (UTC)"
    )
    
    model_version: str = Field(
        ...,
        description="Model version used for prediction"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "prediction": 1,
                "failure_probability": 0.85,
                "severity": "HIGH",
                "days_until_failure": 15,
                "confidence": "high",
                "timestamp": "2025-11-02T10:30:00Z",
                "model_version": "v1"
            }
        }
    )


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""
    
    readings: list[SensorData] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of sensor readings (max 100)"
    )


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""
    
    predictions: list[PredictionResponse] = Field(
        ...,
        description="List of predictions for each reading"
    )
    
    total: int = Field(
        ...,
        description="Total number of predictions"
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    service: str = Field(
        ...,
        description="Service name"
    )
    
    status: str = Field(
        ...,
        description="Service status (healthy/unhealthy)"
    )
    
    version: str = Field(
        ...,
        description="Service version"
    )
    
    model_loaded: bool = Field(
        ...,
        description="Whether ML model is loaded"
    )
    
    model_version: Optional[str] = Field(
        None,
        description="Loaded model version"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )


class ModelInfoResponse(BaseModel):
    """Model information response."""
    
    model_type: str = Field(
        ...,
        description="Type of ML model"
    )
    
    version: str = Field(
        ...,
        description="Model version"
    )
    
    trained_date: str = Field(
        ...,
        description="Training date (ISO format)"
    )
    
    features: list[str] = Field(
        ...,
        description="List of feature names"
    )
    
    accuracy: float = Field(
        ...,
        description="Model accuracy on test set"
    )
    
    precision: float = Field(
        ...,
        description="Model precision"
    )
    
    recall: float = Field(
        ...,
        description="Model recall"
    )
    
    f1_score: float = Field(
        ...,
        description="Model F1 score"
    )
    
    roc_auc: float = Field(
        ...,
        description="Model ROC-AUC score"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(
        ...,
        description="Error type"
    )
    
    detail: str = Field(
        ...,
        description="Error details"
    )
    
    status_code: int = Field(
        ...,
        description="HTTP status code"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )


class SensorReadingInput(BaseModel):
    """
    Simplified sensor reading input (no equipment_id).
    
    For direct prediction endpoint that doesn't require equipment tracking.
    """
    
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=200.0,
        description="Temperature in Celsius",
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
        description="Pressure in bar",
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
        description="Voltage in volts",
        examples=[220.0]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "temperature": 85.5,
                "vibration": 0.45,
                "pressure": 3.2,
                "humidity": 65.0,
                "voltage": 220.0
            }
        }
    )


class SimplePredictionResponse(BaseModel):
    """
    Simplified prediction response (no equipment_id).
    
    For direct prediction endpoint.
    """
    
    failure_probability: float = Field(
        ...,
        description="Probability of failure (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    severity: str = Field(
        ...,
        description="Failure severity level",
        examples=["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    )
    
    days_until_failure: int = Field(
        ...,
        description="Estimated days until failure",
        ge=0
    )
    
    health_score: float = Field(
        ...,
        description="Equipment health score (0-100)",
        ge=0.0,
        le=100.0
    )
    
    confidence: str = Field(
        ...,
        description="Prediction confidence level",
        examples=["high", "medium", "low"]
    )
    
    recommended_action: str = Field(
        ...,
        description="Recommended maintenance action"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Prediction timestamp (UTC)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "failure_probability": 0.82,
                "severity": "CRITICAL",
                "days_until_failure": 7,
                "health_score": 18.0,
                "confidence": "high",
                "recommended_action": "Schedule immediate maintenance - equipment likely to fail within 7 days",
                "timestamp": "2025-11-02T10:30:00Z"
            }
        }
    )


class EquipmentHealthResponse(BaseModel):
    """Response model for equipment health check."""
    
    equipment_id: str = Field(
        ...,
        description="Equipment identifier"
    )
    
    health_score: float = Field(
        ...,
        description="Current health score (0-100)",
        ge=0.0,
        le=100.0
    )
    
    status: str = Field(
        ...,
        description="Overall status",
        examples=["HEALTHY", "WARNING", "CRITICAL"]
    )
    
    last_check: datetime = Field(
        ...,
        description="Last health check timestamp"
    )
    
    next_maintenance: Optional[datetime] = Field(
        None,
        description="Recommended next maintenance date"
    )
    
    failure_probability: float = Field(
        ...,
        description="Current failure probability",
        ge=0.0,
        le=1.0
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "health_score": 75.5,
                "status": "HEALTHY",
                "last_check": "2025-11-02T10:30:00Z",
                "next_maintenance": "2025-11-15T08:00:00Z",
                "failure_probability": 0.24
            }
        }
    )
