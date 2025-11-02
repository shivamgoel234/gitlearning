"""
Business logic for Alert & Maintenance Service.

Handles alert generation, acknowledgment, and maintenance scheduling.
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from .models import AlertResponse, MaintenanceScheduleResponse
from .database import AlertDB, MaintenanceScheduleDB
from .config import settings

logger = logging.getLogger(__name__)


class AlertMaintenanceService:
    """Service class for alert and maintenance operations."""
    
    def __init__(self):
        """Initialize service with Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
    
    async def init_redis(self) -> None:
        """Initialize Redis connection and subscribe to prediction events."""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection initialized")
            
            # Start listening to prediction events in background
            # In production, this would be a separate worker process
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}", exc_info=True)
            raise
    
    async def close_redis(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def create_alert(
        self,
        equipment_id: str,
        prediction_id: str,
        severity: str,
        failure_probability: float,
        db: AsyncSession
    ) -> AlertResponse:
        """
        Create alert based on prediction.
        
        Args:
            equipment_id: Equipment identifier
            prediction_id: Related prediction ID
            severity: Alert severity level
            failure_probability: Failure probability
            db: Database session
            
        Returns:
            AlertResponse with alert details
        """
        try:
            alert_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Generate alert message
            message = self._generate_alert_message(severity, failure_probability)
            
            # Create database record
            db_alert = AlertDB(
                id=alert_id,
                equipment_id=equipment_id,
                prediction_id=prediction_id,
                timestamp=timestamp,
                severity=severity,
                failure_probability=failure_probability,
                message=message,
                acknowledged=False
            )
            
            db.add(db_alert)
            await db.commit()
            await db.refresh(db_alert)
            
            logger.info(
                f"Alert created: alert_id={alert_id}, "
                f"equipment_id={equipment_id}, severity={severity}"
            )
            
            # Publish alert event
            await self._publish_alert_event(alert_id, equipment_id, severity, message)
            
            return AlertResponse(
                alert_id=alert_id,
                equipment_id=equipment_id,
                severity=severity,
                message=message,
                failure_probability=failure_probability,
                acknowledged=False,
                timestamp=timestamp
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create alert: {e}", exc_info=True)
            raise
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: Optional[str],
        db: AsyncSession
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert identifier
            acknowledged_by: User acknowledging the alert
            notes: Optional notes
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            stmt = select(AlertDB).where(AlertDB.id == alert_id)
            result = await db.execute(stmt)
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise ValueError(f"Alert not found: {alert_id}")
            
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            await db.commit()
            
            logger.info(f"Alert acknowledged: alert_id={alert_id}, by={acknowledged_by}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to acknowledge alert: {e}", exc_info=True)
            raise
    
    async def schedule_maintenance(
        self,
        equipment_id: str,
        alert_id: Optional[str],
        scheduled_date: datetime,
        priority: str,
        task_type: str,
        description: str,
        db: AsyncSession
    ) -> MaintenanceScheduleResponse:
        """
        Schedule maintenance for equipment.
        
        Args:
            equipment_id: Equipment identifier
            alert_id: Related alert ID (optional)
            scheduled_date: Scheduled date
            priority: Priority level
            task_type: Type of maintenance
            description: Task description
            db: Database session
            
        Returns:
            MaintenanceScheduleResponse with schedule details
        """
        try:
            schedule_id = str(uuid.uuid4())
            
            # Create database record
            db_schedule = MaintenanceScheduleDB(
                id=schedule_id,
                equipment_id=equipment_id,
                alert_id=alert_id,
                scheduled_date=scheduled_date,
                priority=priority,
                task_type=task_type,
                description=description,
                status="SCHEDULED",
                completed=False
            )
            
            db.add(db_schedule)
            await db.commit()
            await db.refresh(db_schedule)
            
            logger.info(
                f"Maintenance scheduled: schedule_id={schedule_id}, "
                f"equipment_id={equipment_id}, date={scheduled_date}"
            )
            
            return MaintenanceScheduleResponse(
                schedule_id=schedule_id,
                equipment_id=equipment_id,
                scheduled_date=scheduled_date,
                priority=priority,
                task_type=task_type,
                description=description,
                status="SCHEDULED",
                completed=False
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to schedule maintenance: {e}", exc_info=True)
            raise
    
    async def auto_schedule_from_prediction(
        self,
        equipment_id: str,
        severity: str,
        days_until_failure: int,
        db: AsyncSession
    ) -> MaintenanceScheduleResponse:
        """
        Automatically schedule maintenance based on prediction.
        
        Args:
            equipment_id: Equipment identifier
            severity: Severity level
            days_until_failure: Estimated days until failure
            db: Database session
            
        Returns:
            MaintenanceScheduleResponse
        """
        # Calculate scheduled date (schedule before estimated failure)
        buffer_days = max(1, days_until_failure // 2)
        scheduled_date = datetime.utcnow() + timedelta(days=buffer_days)
        
        # Determine task type based on severity
        task_type = "EMERGENCY" if severity == "CRITICAL" else "PREVENTIVE"
        
        description = (
            f"Auto-scheduled {severity.lower()} priority maintenance. "
            f"Estimated failure in {days_until_failure} days. "
            f"Inspect and service equipment to prevent failure."
        )
        
        return await self.schedule_maintenance(
            equipment_id=equipment_id,
            alert_id=None,
            scheduled_date=scheduled_date,
            priority=severity,
            task_type=task_type,
            description=description,
            db=db
        )
    
    def _generate_alert_message(self, severity: str, failure_probability: float) -> str:
        """Generate human-readable alert message."""
        prob_percent = int(failure_probability * 100)
        
        if severity == "CRITICAL":
            return f"CRITICAL: {prob_percent}% failure risk - immediate action required"
        elif severity == "HIGH":
            return f"HIGH: {prob_percent}% failure risk - schedule maintenance soon"
        elif severity == "MEDIUM":
            return f"MEDIUM: {prob_percent}% failure risk - plan maintenance"
        else:
            return f"LOW: {prob_percent}% failure risk - routine monitoring"
    
    async def _publish_alert_event(
        self,
        alert_id: str,
        equipment_id: str,
        severity: str,
        message: str
    ) -> None:
        """Publish alert event to Redis pub/sub."""
        if not self.redis_client:
            logger.warning("Redis client not initialized, skipping event publish")
            return
        
        try:
            event_data = {
                "event_type": "alert_created",
                "alert_id": alert_id,
                "equipment_id": equipment_id,
                "severity": severity,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(
                "alert_channel",
                json.dumps(event_data)
            )
            
            logger.debug(f"Published alert event for equipment_id={equipment_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish alert event: {e}", exc_info=True)


# Global service instance
alert_service = AlertMaintenanceService()
