"""
Pydantic models for Dashboard Service API.

Defines request/response schemas for dashboard data.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class EquipmentOverview(BaseModel):
    """Equipment overview model."""
    equipment_id: str
    health_score: float
    status: str
    last_reading: datetime
    alert_count: int
    maintenance_scheduled: bool


class DashboardSummary(BaseModel):
    """Dashboard summary response."""
    total_equipment: int
    critical_alerts: int
    pending_maintenance: int
    average_health_score: float
    equipment_by_status: dict
    recent_alerts: List[dict]
    timestamp: datetime


class EquipmentDetail(BaseModel):
    """Detailed equipment information."""
    equipment_id: str
    health_score: float
    status: str
    latest_sensor_data: dict
    latest_prediction: Optional[dict]
    active_alerts: List[dict]
    maintenance_schedule: List[dict]
    trend_data: List[dict]


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(..., description="Current timestamp")
    database: Optional[str] = Field(None, description="Database connection status")
    redis: Optional[str] = Field(None, description="Redis connection status")
    upstream_services: Optional[dict] = Field(None, description="Upstream service status")


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="Error timestamp")
