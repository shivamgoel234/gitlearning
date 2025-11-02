"""
SQLAlchemy database models for Alert & Maintenance service.

Defines database schema for alerts and maintenance tasks with proper
indexing, relationships, and constraints.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime

# Create declarative base
Base = declarative_base()


class AlertDB(Base):
    """
    Database model for equipment failure alerts.
    
    Stores alerts generated from ML predictions about potential
    equipment failures. Alerts can be acknowledged and resolved
    by maintenance staff.
    """
    
    __tablename__ = "alerts"
    
    # Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique alert identifier (UUID)"
    )
    
    # Equipment Information
    equipment_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Equipment identifier (e.g., RADAR-LOC-001)"
    )
    
    # Alert Details
    severity = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Alert severity: CRITICAL, HIGH, MEDIUM, LOW"
    )
    
    failure_probability = Column(
        Float,
        nullable=False,
        comment="Predicted failure probability (0.0 to 1.0)"
    )
    
    days_until_failure = Column(
        Integer,
        nullable=False,
        comment="Estimated days until equipment failure"
    )
    
    recommended_action = Column(
        String(500),
        nullable=False,
        comment="Recommended maintenance action"
    )
    
    # Alert Status
    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False,
        index=True,
        comment="Alert status: ACTIVE, ACKNOWLEDGED, RESOLVED"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When alert was created"
    )
    
    acknowledged_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When alert was acknowledged"
    )
    
    acknowledged_by = Column(
        String(100),
        nullable=True,
        comment="User who acknowledged the alert"
    )
    
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When alert was resolved"
    )
    
    resolved_by = Column(
        String(100),
        nullable=True,
        comment="User who resolved the alert"
    )
    
    # Additional Information
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes about the alert"
    )
    
    health_score = Column(
        Float,
        nullable=True,
        comment="Equipment health score at time of alert (0-100)"
    )
    
    confidence = Column(
        String(20),
        nullable=True,
        comment="Prediction confidence: high, medium, low"
    )
    
    # Metadata
    source = Column(
        String(50),
        default="ml_prediction",
        nullable=False,
        comment="Source of alert: ml_prediction, manual, scheduled"
    )
    
    alert_type = Column(
        String(50),
        default="predictive",
        nullable=False,
        comment="Type of alert: predictive, threshold, anomaly"
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_equipment_status', 'equipment_id', 'status'),
        Index('idx_severity_created', 'severity', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self) -> str:
        """String representation of Alert."""
        return (
            f"<Alert(id={self.id}, equipment_id={self.equipment_id}, "
            f"severity={self.severity}, status={self.status})>"
        )


class MaintenanceTaskDB(Base):
    """
    Database model for maintenance tasks.
    
    Stores scheduled and completed maintenance tasks for equipment.
    Tasks can be created automatically from alerts or manually by staff.
    """
    
    __tablename__ = "maintenance_tasks"
    
    # Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique task identifier (UUID)"
    )
    
    # Equipment Information
    equipment_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Equipment identifier (e.g., RADAR-LOC-001)"
    )
    
    # Task Classification
    task_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Task type: ROUTINE, PREVENTIVE, CORRECTIVE, EMERGENCY"
    )
    
    priority = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Task priority: LOW, MEDIUM, HIGH, CRITICAL"
    )
    
    # Scheduling
    scheduled_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When maintenance is scheduled"
    )
    
    completed_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When maintenance was completed"
    )
    
    due_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Latest date task should be completed"
    )
    
    # Task Status
    status = Column(
        String(20),
        default="SCHEDULED",
        nullable=False,
        index=True,
        comment="Task status: SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, OVERDUE"
    )
    
    # Assignment
    assigned_to = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User or team assigned to task"
    )
    
    assigned_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When task was assigned"
    )
    
    # Time Estimates
    estimated_duration_hours = Column(
        Integer,
        nullable=True,
        comment="Estimated task duration in hours"
    )
    
    actual_duration_hours = Column(
        Integer,
        nullable=True,
        comment="Actual task duration in hours"
    )
    
    # Cost Estimates
    cost_estimate = Column(
        Float,
        nullable=True,
        comment="Estimated cost in currency units"
    )
    
    actual_cost = Column(
        Float,
        nullable=True,
        comment="Actual cost in currency units"
    )
    
    # Task Details
    title = Column(
        String(200),
        nullable=True,
        comment="Brief task title"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed task description"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes and comments"
    )
    
    completion_notes = Column(
        Text,
        nullable=True,
        comment="Notes about task completion"
    )
    
    # Related Alert
    alert_id = Column(
        String(36),
        nullable=True,
        index=True,
        comment="ID of related alert (if any)"
    )
    
    # Parts and Resources
    parts_required = Column(
        Text,
        nullable=True,
        comment="List of parts/materials needed (JSON)"
    )
    
    parts_cost = Column(
        Float,
        nullable=True,
        comment="Cost of parts/materials"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When task was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When task was last updated"
    )
    
    created_by = Column(
        String(100),
        nullable=True,
        comment="User who created the task"
    )
    
    # Metadata
    source = Column(
        String(50),
        default="manual",
        nullable=False,
        comment="Source of task: manual, auto_alert, scheduled"
    )
    
    recurrence_pattern = Column(
        String(100),
        nullable=True,
        comment="Recurrence pattern for routine tasks (e.g., weekly, monthly)"
    )
    
    parent_task_id = Column(
        String(36),
        nullable=True,
        comment="ID of parent task (for recurring tasks)"
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_equipment_status', 'equipment_id', 'status'),
        Index('idx_priority_scheduled', 'priority', 'scheduled_date'),
        Index('idx_status_scheduled', 'status', 'scheduled_date'),
        Index('idx_assigned_status', 'assigned_to', 'status'),
        Index('idx_alert_task', 'alert_id'),
    )
    
    def __repr__(self) -> str:
        """String representation of MaintenanceTask."""
        return (
            f"<MaintenanceTask(id={self.id}, equipment_id={self.equipment_id}, "
            f"type={self.task_type}, priority={self.priority}, status={self.status})>"
        )


class MaintenanceHistoryDB(Base):
    """
    Database model for maintenance history log.
    
    Stores historical record of all maintenance activities for
    audit trail and analysis purposes.
    """
    
    __tablename__ = "maintenance_history"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique history entry identifier"
    )
    
    task_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="Related maintenance task ID"
    )
    
    equipment_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Equipment identifier"
    )
    
    action = Column(
        String(50),
        nullable=False,
        comment="Action performed: created, assigned, started, completed, cancelled"
    )
    
    performed_by = Column(
        String(100),
        nullable=True,
        comment="User who performed the action"
    )
    
    performed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When action was performed"
    )
    
    details = Column(
        Text,
        nullable=True,
        comment="Additional details about the action"
    )
    
    old_status = Column(
        String(20),
        nullable=True,
        comment="Previous status (for status changes)"
    )
    
    new_status = Column(
        String(20),
        nullable=True,
        comment="New status (for status changes)"
    )
    
    __table_args__ = (
        Index('idx_task_performed', 'task_id', 'performed_at'),
        Index('idx_equipment_performed', 'equipment_id', 'performed_at'),
    )
    
    def __repr__(self) -> str:
        """String representation of MaintenanceHistory."""
        return (
            f"<MaintenanceHistory(id={self.id}, task_id={self.task_id}, "
            f"action={self.action})>"
        )
