"""
Pydantic models for Alert & Maintenance Service API.

Defines request/response schemas with validation rules.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class AlertRequest(BaseModel):
    """Request model for alert creation."""
    equipment_id: str = Field(..., description="Equipment identifier")
    prediction_id: str = Field(..., description="Related prediction ID")
    severity: str = Field(..., description="Alert severity")
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    
    @field_validator('equipment_id')
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        """Validate and normalize equipment ID."""
        return v.upper()


class AlertResponse(BaseModel):
    """Response model for alert."""
    alert_id: str = Field(..., description="Unique alert identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    failure_probability: float = Field(..., description="Failure probability")
    acknowledged: bool = Field(..., description="Acknowledgment status")
    timestamp: datetime = Field(..., description="Alert timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert-123",
                "equipment_id": "RADAR-LOC-001",
                "severity": "HIGH",
                "message": "High failure risk detected - schedule maintenance",
                "failure_probability": 0.75,
                "acknowledged": False,
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }


class AcknowledgeAlertRequest(BaseModel):
    """Request model for acknowledging alert."""
    acknowledged_by: str = Field(..., max_length=100, description="User who acknowledged")
    notes: Optional[str] = Field(None, description="Optional notes")


class MaintenanceScheduleRequest(BaseModel):
    """Request model for scheduling maintenance."""
    equipment_id: str = Field(..., description="Equipment identifier")
    scheduled_date: datetime = Field(..., description="Scheduled maintenance date")
    priority: str = Field(..., description="Priority level")
    task_type: str = Field(..., description="Type of maintenance task")
    description: str = Field(..., description="Task description")
    
    @field_validator('equipment_id')
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        """Validate and normalize equipment ID."""
        return v.upper()


class MaintenanceScheduleResponse(BaseModel):
    """Response model for maintenance schedule."""
    schedule_id: str = Field(..., description="Unique schedule identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    scheduled_date: datetime = Field(..., description="Scheduled date")
    priority: str = Field(..., description="Priority level")
    task_type: str = Field(..., description="Task type")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Schedule status")
    completed: bool = Field(..., description="Completion status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "maint-123",
                "equipment_id": "RADAR-LOC-001",
                "scheduled_date": "2025-01-15T09:00:00Z",
                "priority": "HIGH",
                "task_type": "PREVENTIVE",
                "description": "Inspect and replace worn components",
                "status": "SCHEDULED",
                "completed": False
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
