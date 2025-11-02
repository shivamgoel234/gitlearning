"""
Pydantic models for API request and response validation.

Defines data models for alert and maintenance task operations with
comprehensive validation, examples, and documentation.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AlertStatus(str, Enum):
    """Alert status values."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class TaskType(str, Enum):
    """Maintenance task types."""
    ROUTINE = "ROUTINE"
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    EMERGENCY = "EMERGENCY"


class TaskPriority(str, Enum):
    """Maintenance task priorities."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    """Maintenance task status values."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


# ============================================================================
# ALERT MODELS
# ============================================================================

class AlertCreate(BaseModel):
    """
    Request model for creating a new alert.
    
    Used when ML prediction service or monitoring system
    detects a potential equipment failure.
    """
    
    equipment_id: str = Field(
        ...,
        description="Equipment identifier (e.g., RADAR-LOC-001)",
        min_length=3,
        max_length=100,
        examples=["RADAR-LOC-001"]
    )
    
    severity: AlertSeverity = Field(
        ...,
        description="Alert severity level"
    )
    
    failure_probability: float = Field(
        ...,
        description="Predicted failure probability (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.82]
    )
    
    days_until_failure: int = Field(
        ...,
        description="Estimated days until equipment failure",
        ge=0,
        examples=[7]
    )
    
    recommended_action: str = Field(
        ...,
        description="Recommended maintenance action",
        min_length=10,
        max_length=500,
        examples=["Schedule immediate maintenance - equipment likely to fail within 7 days"]
    )
    
    health_score: Optional[float] = Field(
        None,
        description="Equipment health score (0-100)",
        ge=0.0,
        le=100.0,
        examples=[18.0]
    )
    
    confidence: Optional[str] = Field(
        None,
        description="Prediction confidence level",
        examples=["high"]
    )
    
    source: Optional[str] = Field(
        "ml_prediction",
        description="Source of alert",
        examples=["ml_prediction", "manual", "threshold"]
    )
    
    alert_type: Optional[str] = Field(
        "predictive",
        description="Type of alert",
        examples=["predictive", "threshold", "anomaly"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "severity": "CRITICAL",
                "failure_probability": 0.82,
                "days_until_failure": 7,
                "recommended_action": "Schedule immediate maintenance - equipment likely to fail within 7 days",
                "health_score": 18.0,
                "confidence": "high",
                "source": "ml_prediction",
                "alert_type": "predictive"
            }
        }
    )


class AlertUpdate(BaseModel):
    """
    Request model for updating an existing alert.
    
    Used to acknowledge or resolve alerts, add notes, etc.
    """
    
    status: Optional[AlertStatus] = Field(
        None,
        description="New alert status"
    )
    
    acknowledged_by: Optional[str] = Field(
        None,
        description="User who acknowledged the alert",
        examples=["john.doe@drdo.gov.in"]
    )
    
    resolved_by: Optional[str] = Field(
        None,
        description="User who resolved the alert",
        examples=["jane.smith@drdo.gov.in"]
    )
    
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the alert",
        examples=["Maintenance team contacted. Work order created."]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ACKNOWLEDGED",
                "acknowledged_by": "john.doe@drdo.gov.in",
                "notes": "Maintenance team contacted. Work order #12345 created."
            }
        }
    )


class AlertResponse(BaseModel):
    """
    Response model for alert data.
    
    Returned when retrieving alert information.
    """
    
    id: str = Field(..., description="Unique alert identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    severity: str = Field(..., description="Alert severity")
    failure_probability: float = Field(..., description="Failure probability")
    days_until_failure: int = Field(..., description="Days until failure")
    recommended_action: str = Field(..., description="Recommended action")
    status: str = Field(..., description="Alert status")
    created_at: datetime = Field(..., description="Creation timestamp")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolved_by: Optional[str] = Field(None, description="User who resolved")
    notes: Optional[str] = Field(None, description="Additional notes")
    health_score: Optional[float] = Field(None, description="Health score")
    confidence: Optional[str] = Field(None, description="Confidence level")
    source: Optional[str] = Field(None, description="Alert source")
    alert_type: Optional[str] = Field(None, description="Alert type")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "equipment_id": "RADAR-LOC-001",
                "severity": "CRITICAL",
                "failure_probability": 0.82,
                "days_until_failure": 7,
                "recommended_action": "Schedule immediate maintenance",
                "status": "ACTIVE",
                "created_at": "2025-11-02T10:30:00Z",
                "acknowledged_at": None,
                "acknowledged_by": None,
                "resolved_at": None,
                "resolved_by": None,
                "notes": None,
                "health_score": 18.0,
                "confidence": "high",
                "source": "ml_prediction",
                "alert_type": "predictive"
            }
        }
    )


class AlertListResponse(BaseModel):
    """Response model for list of alerts."""
    
    alerts: List[AlertResponse] = Field(..., description="List of alerts")
    total: int = Field(..., description="Total number of alerts")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")


# ============================================================================
# MAINTENANCE TASK MODELS
# ============================================================================

class MaintenanceTaskCreate(BaseModel):
    """
    Request model for creating a new maintenance task.
    
    Can be created manually or automatically from an alert.
    """
    
    equipment_id: str = Field(
        ...,
        description="Equipment identifier",
        min_length=3,
        max_length=100,
        examples=["RADAR-LOC-001"]
    )
    
    task_type: TaskType = Field(
        ...,
        description="Type of maintenance task"
    )
    
    priority: TaskPriority = Field(
        ...,
        description="Task priority level"
    )
    
    scheduled_date: datetime = Field(
        ...,
        description="When maintenance is scheduled"
    )
    
    title: Optional[str] = Field(
        None,
        description="Brief task title",
        max_length=200,
        examples=["Replace cooling system filters"]
    )
    
    description: Optional[str] = Field(
        None,
        description="Detailed task description",
        examples=["Replace all cooling system filters due to predicted failure"]
    )
    
    estimated_duration_hours: Optional[int] = Field(
        None,
        description="Estimated duration in hours",
        ge=0,
        examples=[4]
    )
    
    cost_estimate: Optional[float] = Field(
        None,
        description="Estimated cost",
        ge=0.0,
        examples=[5000.0]
    )
    
    assigned_to: Optional[str] = Field(
        None,
        description="User or team assigned to task",
        examples=["maintenance-team-a@drdo.gov.in"]
    )
    
    notes: Optional[str] = Field(
        None,
        description="Additional notes",
        examples=["High priority - equipment showing signs of failure"]
    )
    
    alert_id: Optional[str] = Field(
        None,
        description="Related alert ID (if any)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    parts_required: Optional[str] = Field(
        None,
        description="Required parts/materials (JSON)",
        examples=['["Filter Model ABC-123", "Coolant Type XYZ"]']
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "equipment_id": "RADAR-LOC-001",
                "task_type": "PREVENTIVE",
                "priority": "CRITICAL",
                "scheduled_date": "2025-11-09T08:00:00Z",
                "title": "Emergency cooling system maintenance",
                "description": "Replace cooling system filters due to predicted failure",
                "estimated_duration_hours": 4,
                "cost_estimate": 5000.0,
                "assigned_to": "maintenance-team-a@drdo.gov.in",
                "notes": "High priority - equipment showing signs of imminent failure",
                "alert_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class MaintenanceTaskUpdate(BaseModel):
    """
    Request model for updating a maintenance task.
    
    Used to update status, assignment, completion details, etc.
    """
    
    status: Optional[TaskStatus] = Field(
        None,
        description="New task status"
    )
    
    assigned_to: Optional[str] = Field(
        None,
        description="Assigned user/team"
    )
    
    scheduled_date: Optional[datetime] = Field(
        None,
        description="New scheduled date"
    )
    
    completed_date: Optional[datetime] = Field(
        None,
        description="Completion date"
    )
    
    actual_duration_hours: Optional[int] = Field(
        None,
        description="Actual duration in hours",
        ge=0
    )
    
    actual_cost: Optional[float] = Field(
        None,
        description="Actual cost",
        ge=0.0
    )
    
    notes: Optional[str] = Field(
        None,
        description="Additional notes"
    )
    
    completion_notes: Optional[str] = Field(
        None,
        description="Completion notes"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "COMPLETED",
                "completed_date": "2025-11-09T14:00:00Z",
                "actual_duration_hours": 5,
                "actual_cost": 5500.0,
                "completion_notes": "Maintenance completed successfully. All filters replaced."
            }
        }
    )


class MaintenanceTaskResponse(BaseModel):
    """
    Response model for maintenance task data.
    
    Returned when retrieving task information.
    """
    
    id: str = Field(..., description="Unique task identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    task_type: str = Field(..., description="Task type")
    priority: str = Field(..., description="Task priority")
    scheduled_date: datetime = Field(..., description="Scheduled date")
    status: str = Field(..., description="Task status")
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    assigned_to: Optional[str] = Field(None, description="Assigned to")
    assigned_at: Optional[datetime] = Field(None, description="Assignment timestamp")
    completed_date: Optional[datetime] = Field(None, description="Completion date")
    estimated_duration_hours: Optional[int] = Field(None, description="Estimated duration")
    actual_duration_hours: Optional[int] = Field(None, description="Actual duration")
    cost_estimate: Optional[float] = Field(None, description="Cost estimate")
    actual_cost: Optional[float] = Field(None, description="Actual cost")
    notes: Optional[str] = Field(None, description="Notes")
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    alert_id: Optional[str] = Field(None, description="Related alert ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Created by")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440001",
                "equipment_id": "RADAR-LOC-001",
                "task_type": "PREVENTIVE",
                "priority": "CRITICAL",
                "scheduled_date": "2025-11-09T08:00:00Z",
                "status": "SCHEDULED",
                "title": "Emergency cooling system maintenance",
                "description": "Replace cooling system filters",
                "assigned_to": "maintenance-team-a@drdo.gov.in",
                "assigned_at": "2025-11-02T10:35:00Z",
                "completed_date": None,
                "estimated_duration_hours": 4,
                "actual_duration_hours": None,
                "cost_estimate": 5000.0,
                "actual_cost": None,
                "notes": "High priority task",
                "completion_notes": None,
                "alert_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-11-02T10:30:00Z",
                "updated_at": "2025-11-02T10:35:00Z",
                "created_by": "system"
            }
        }
    )


class MaintenanceTaskListResponse(BaseModel):
    """Response model for list of maintenance tasks."""
    
    tasks: List[MaintenanceTaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")


# ============================================================================
# HEALTH CHECK MODELS
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    database_connected: bool = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Check timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "alert-maintenance-service",
                "status": "healthy",
                "version": "1.0.0",
                "database_connected": True,
                "timestamp": "2025-11-02T10:30:00Z"
            }
        }
    )


# ============================================================================
# STATISTICS MODELS
# ============================================================================

class AlertStatistics(BaseModel):
    """Statistics about alerts."""
    
    total_alerts: int = Field(..., description="Total number of alerts")
    active_alerts: int = Field(..., description="Number of active alerts")
    critical_alerts: int = Field(..., description="Number of critical alerts")
    acknowledged_alerts: int = Field(..., description="Number of acknowledged alerts")
    resolved_alerts: int = Field(..., description="Number of resolved alerts")
    average_resolution_time_hours: Optional[float] = Field(None, description="Average resolution time")


class TaskStatistics(BaseModel):
    """Statistics about maintenance tasks."""
    
    total_tasks: int = Field(..., description="Total number of tasks")
    scheduled_tasks: int = Field(..., description="Number of scheduled tasks")
    in_progress_tasks: int = Field(..., description="Number of in-progress tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    overdue_tasks: int = Field(..., description="Number of overdue tasks")
    average_completion_time_hours: Optional[float] = Field(None, description="Average completion time")


# ============================================================================
# ERROR RESPONSE MODEL
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "detail": "Equipment ID format is invalid",
                "status_code": 422,
                "timestamp": "2025-11-02T10:30:00Z"
            }
        }
    )
