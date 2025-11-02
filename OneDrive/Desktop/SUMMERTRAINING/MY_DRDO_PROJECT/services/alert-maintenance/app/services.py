"""
Business logic services for Alert & Maintenance microservice.

Provides alert generation from ML predictions and maintenance task creation.
Simplified implementation for demo/MVP purposes.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .schemas import AlertDB, MaintenanceTaskDB
from .config import settings

logger = logging.getLogger(__name__)


class AlertGenerationService:
    """
    Service for generating alerts from ML predictions.
    
    This service acts as a bridge between the ML Prediction service
    and the Alert & Maintenance database. It fetches predictions and
    creates alerts for equipment that shows signs of failure.
    """
    
    def __init__(self, db_session: AsyncSession, ml_service_url: Optional[str] = None):
        """
        Initialize alert generation service.
        
        Args:
            db_session: Async database session
            ml_service_url: URL of ML prediction service (defaults to settings)
        """
        self.db = db_session
        self.ml_service_url = ml_service_url or settings.ML_PREDICTION_SERVICE_URL
        logger.debug(f"AlertGenerationService initialized with ML service: {self.ml_service_url}")
    
    async def call_ml_prediction(self, sensor_data: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Call ML prediction service and return prediction result.
        
        Makes HTTP POST request to ML service with sensor data and
        returns the prediction response.
        
        Args:
            sensor_data: Dictionary with sensor readings:
                - temperature: float
                - vibration: float
                - pressure: float
                - humidity: float (optional)
                - voltage: float (optional)
        
        Returns:
            Prediction dictionary with:
                - failure_probability: float
                - severity: str (CRITICAL, HIGH, MEDIUM, LOW)
                - days_until_failure: int
                - health_score: float
                - confidence: str
                - recommended_action: str
            Or None if call fails
            
        Example:
            >>> service = AlertGenerationService(db)
            >>> sensor_data = {
            ...     "temperature": 85.5,
            ...     "vibration": 0.45,
            ...     "pressure": 3.2
            ... }
            >>> prediction = await service.call_ml_prediction(sensor_data)
            >>> if prediction:
            ...     print(f"Failure probability: {prediction['failure_probability']}")
        """
        endpoint = f"{self.ml_service_url}/api/v1/predict/failure"
        
        logger.info(f"Calling ML prediction service: {endpoint}")
        logger.debug(f"Sensor data: {sensor_data}")
        
        try:
            # Make async HTTP request with timeout
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    endpoint,
                    json=sensor_data,
                    headers={"Content-Type": "application/json"}
                )
                
                # Check response status
                if response.status_code == 200:
                    prediction = response.json()
                    logger.info(
                        f"ML prediction received: "
                        f"severity={prediction.get('severity')}, "
                        f"probability={prediction.get('failure_probability')}"
                    )
                    return prediction
                else:
                    logger.error(
                        f"ML service returned error: "
                        f"status={response.status_code}, "
                        f"body={response.text}"
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"ML service call timed out after 5 seconds: {endpoint}")
            return None
            
        except httpx.RequestError as e:
            logger.error(f"ML service request failed: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error calling ML service: {str(e)}", exc_info=True)
            return None
    
    async def create_alert(
        self, 
        equipment_id: str, 
        prediction: Dict[str, Any]
    ) -> AlertDB:
        """
        Create alert in database from prediction result.
        
        Creates a new alert record with ACTIVE status and stores all
        prediction data for tracking and reporting.
        
        Args:
            equipment_id: Equipment identifier (e.g., RADAR-LOC-001)
            prediction: Prediction dictionary from ML service
        
        Returns:
            Created AlertDB object with all fields populated
            
        Raises:
            Exception: If database operation fails
            
        Example:
            >>> prediction = {
            ...     "severity": "CRITICAL",
            ...     "failure_probability": 0.82,
            ...     "days_until_failure": 7,
            ...     "recommended_action": "Schedule immediate maintenance",
            ...     "health_score": 18.0,
            ...     "confidence": "high"
            ... }
            >>> alert = await service.create_alert("RADAR-LOC-001", prediction)
            >>> print(f"Alert created: {alert.id}")
        """
        logger.info(f"Creating alert for equipment: {equipment_id}")
        
        # Create alert object
        alert = AlertDB(
            id=str(uuid.uuid4()),
            equipment_id=equipment_id,
            severity=prediction.get("severity", "UNKNOWN"),
            failure_probability=prediction.get("failure_probability", 0.0),
            days_until_failure=prediction.get("days_until_failure", 0),
            recommended_action=prediction.get("recommended_action", "Contact maintenance team"),
            status="ACTIVE",
            health_score=prediction.get("health_score"),
            confidence=prediction.get("confidence"),
            source="ml_prediction",
            alert_type="predictive",
            created_at=datetime.utcnow()
        )
        
        try:
            # Add to session and commit
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(
                f"✓ Alert created successfully: "
                f"id={alert.id}, "
                f"equipment={alert.equipment_id}, "
                f"severity={alert.severity}"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert in database: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def generate_alert_for_equipment(
        self,
        equipment_id: str,
        sensor_data: Dict[str, float]
    ) -> Optional[AlertDB]:
        """
        Main method: Get prediction and create alert if needed.
        
        This is the primary entry point for alert generation. It:
        1. Calls ML service to get failure prediction
        2. Evaluates if alert is needed (CRITICAL or HIGH severity)
        3. Creates alert in database if conditions are met
        4. Returns alert object or None
        
        Args:
            equipment_id: Equipment identifier
            sensor_data: Sensor readings for prediction
        
        Returns:
            AlertDB object if alert was created, None otherwise
            
        Example:
            >>> service = AlertGenerationService(db)
            >>> sensor_data = {
            ...     "temperature": 95.5,
            ...     "vibration": 0.85,
            ...     "pressure": 4.2,
            ...     "humidity": 70.0,
            ...     "voltage": 230.0
            ... }
            >>> alert = await service.generate_alert_for_equipment(
            ...     "RADAR-LOC-001", 
            ...     sensor_data
            ... )
            >>> if alert:
            ...     print(f"ALERT: {alert.severity} - {alert.recommended_action}")
            ... else:
            ...     print("No alert needed")
        """
        logger.info(f"Generating alert for equipment: {equipment_id}")
        
        # Step 1: Get prediction from ML service
        prediction = await self.call_ml_prediction(sensor_data)
        
        if not prediction:
            logger.warning(f"Cannot generate alert for {equipment_id}: ML prediction failed")
            return None
        
        # Step 2: Check if alert is needed (only CRITICAL or HIGH)
        severity = prediction.get("severity", "UNKNOWN")
        
        if severity in ["CRITICAL", "HIGH"]:
            logger.info(
                f"Alert threshold met for {equipment_id}: "
                f"severity={severity}, "
                f"probability={prediction.get('failure_probability')}"
            )
            
            # Step 3: Create alert
            try:
                alert = await self.create_alert(equipment_id, prediction)
                logger.info(f"✓ Alert created: {alert.id} for {equipment_id}")
                return alert
                
            except Exception as e:
                logger.error(f"Failed to create alert for {equipment_id}: {str(e)}")
                return None
        else:
            # No alert needed for MEDIUM or LOW severity
            logger.info(
                f"No alert needed for {equipment_id}: "
                f"severity={severity} (threshold: CRITICAL/HIGH)"
            )
            return None
    
    async def get_alert_by_id(self, alert_id: str) -> Optional[AlertDB]:
        """
        Retrieve alert by ID.
        
        Args:
            alert_id: Alert UUID
        
        Returns:
            AlertDB object or None if not found
        """
        try:
            result = await self.db.execute(
                select(AlertDB).where(AlertDB.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            
            if alert:
                logger.debug(f"Alert found: {alert_id}")
            else:
                logger.debug(f"Alert not found: {alert_id}")
            
            return alert
            
        except Exception as e:
            logger.error(f"Error retrieving alert {alert_id}: {str(e)}")
            return None
    
    async def get_alerts_by_equipment(
        self, 
        equipment_id: str, 
        status: Optional[str] = None
    ) -> list[AlertDB]:
        """
        Get all alerts for specific equipment.
        
        Args:
            equipment_id: Equipment identifier
            status: Optional status filter (ACTIVE, ACKNOWLEDGED, RESOLVED)
        
        Returns:
            List of AlertDB objects
        """
        try:
            query = select(AlertDB).where(AlertDB.equipment_id == equipment_id)
            
            if status:
                query = query.where(AlertDB.status == status)
            
            query = query.order_by(AlertDB.created_at.desc())
            
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            
            logger.info(
                f"Retrieved {len(alerts)} alerts for {equipment_id} "
                f"(status filter: {status or 'none'})"
            )
            
            return list(alerts)
            
        except Exception as e:
            logger.error(f"Error retrieving alerts for {equipment_id}: {str(e)}")
            return []
    
    async def acknowledge_alert(
        self, 
        alert_id: str, 
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> Optional[AlertDB]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert UUID
            acknowledged_by: User/system acknowledging the alert
            notes: Optional acknowledgment notes
        
        Returns:
            Updated AlertDB object or None if not found
        """
        alert = await self.get_alert_by_id(alert_id)
        
        if not alert:
            logger.warning(f"Cannot acknowledge alert: {alert_id} not found")
            return None
        
        try:
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            if notes:
                alert.notes = notes
            
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
            await self.db.rollback()
            return None
    
    async def resolve_alert(
        self, 
        alert_id: str, 
        resolved_by: str,
        notes: Optional[str] = None
    ) -> Optional[AlertDB]:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert UUID
            resolved_by: User/system resolving the alert
            notes: Optional resolution notes
        
        Returns:
            Updated AlertDB object or None if not found
        """
        alert = await self.get_alert_by_id(alert_id)
        
        if not alert:
            logger.warning(f"Cannot resolve alert: {alert_id} not found")
            return None
        
        try:
            alert.status = "RESOLVED"
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            
            if notes:
                current_notes = alert.notes or ""
                alert.notes = f"{current_notes}\nResolution: {notes}".strip()
            
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
            await self.db.rollback()
            return None


class MaintenanceTaskService:
    """
    Service for managing maintenance tasks.
    
    Simplified implementation for creating and managing maintenance
    tasks, optionally linked to alerts.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize maintenance task service.
        
        Args:
            db_session: Async database session
        """
        self.db = db_session
        logger.debug("MaintenanceTaskService initialized")
    
    async def create_task(
        self,
        equipment_id: str,
        task_type: str,
        priority: str,
        scheduled_date: datetime,
        alert_id: Optional[str] = None,
        **kwargs
    ) -> MaintenanceTaskDB:
        """
        Create a new maintenance task.
        
        Args:
            equipment_id: Equipment identifier
            task_type: ROUTINE, PREVENTIVE, CORRECTIVE, EMERGENCY
            priority: LOW, MEDIUM, HIGH, CRITICAL
            scheduled_date: When task should be performed
            alert_id: Optional related alert ID
            **kwargs: Additional task fields (title, description, etc.)
        
        Returns:
            Created MaintenanceTaskDB object
            
        Example:
            >>> service = MaintenanceTaskService(db)
            >>> task = await service.create_task(
            ...     equipment_id="RADAR-LOC-001",
            ...     task_type="PREVENTIVE",
            ...     priority="CRITICAL",
            ...     scheduled_date=datetime.utcnow() + timedelta(days=7),
            ...     title="Emergency cooling system maintenance",
            ...     estimated_duration_hours=4,
            ...     cost_estimate=5000.0
            ... )
        """
        logger.info(f"Creating maintenance task for {equipment_id}")
        
        task = MaintenanceTaskDB(
            id=str(uuid.uuid4()),
            equipment_id=equipment_id,
            task_type=task_type,
            priority=priority,
            scheduled_date=scheduled_date,
            status="SCHEDULED",
            alert_id=alert_id,
            title=kwargs.get("title"),
            description=kwargs.get("description"),
            estimated_duration_hours=kwargs.get("estimated_duration_hours"),
            cost_estimate=kwargs.get("cost_estimate"),
            assigned_to=kwargs.get("assigned_to"),
            notes=kwargs.get("notes"),
            source="auto_alert" if alert_id else "manual",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(
                f"✓ Task created: id={task.id}, "
                f"type={task.task_type}, "
                f"priority={task.priority}"
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def create_task_from_alert(self, alert: AlertDB) -> MaintenanceTaskDB:
        """
        Auto-create maintenance task from critical alert.
        
        Uses alert severity to determine task priority and scheduling.
        
        Args:
            alert: AlertDB object to create task from
        
        Returns:
            Created MaintenanceTaskDB object
        """
        logger.info(f"Creating task from alert: {alert.id}")
        
        # Map severity to priority
        priority = alert.severity  # Direct mapping
        
        # Calculate scheduled date based on days_until_failure
        scheduled_date = datetime.utcnow() + timedelta(days=alert.days_until_failure)
        
        # Determine task type based on severity
        task_type = "EMERGENCY" if alert.severity == "CRITICAL" else "PREVENTIVE"
        
        # Create task
        task = await self.create_task(
            equipment_id=alert.equipment_id,
            task_type=task_type,
            priority=priority,
            scheduled_date=scheduled_date,
            alert_id=alert.id,
            title=f"Address {alert.severity} alert for {alert.equipment_id}",
            description=alert.recommended_action,
            estimated_duration_hours=settings.DEFAULT_TASK_DURATION,
            notes=f"Auto-generated from alert {alert.id}"
        )
        
        logger.info(f"✓ Task created from alert: task_id={task.id}, alert_id={alert.id}")
        return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[MaintenanceTaskDB]:
        """
        Retrieve task by ID.
        
        Args:
            task_id: Task UUID
        
        Returns:
            MaintenanceTaskDB object or None if not found
        """
        try:
            result = await self.db.execute(
                select(MaintenanceTaskDB).where(MaintenanceTaskDB.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                logger.debug(f"Task found: {task_id}")
            else:
                logger.debug(f"Task not found: {task_id}")
            
            return task
            
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {str(e)}")
            return None
    
    async def get_tasks_by_equipment(
        self, 
        equipment_id: str,
        status: Optional[str] = None
    ) -> list[MaintenanceTaskDB]:
        """
        Get all tasks for specific equipment.
        
        Args:
            equipment_id: Equipment identifier
            status: Optional status filter
        
        Returns:
            List of MaintenanceTaskDB objects
        """
        try:
            query = select(MaintenanceTaskDB).where(
                MaintenanceTaskDB.equipment_id == equipment_id
            )
            
            if status:
                query = query.where(MaintenanceTaskDB.status == status)
            
            query = query.order_by(MaintenanceTaskDB.scheduled_date.asc())
            
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            logger.info(
                f"Retrieved {len(tasks)} tasks for {equipment_id} "
                f"(status filter: {status or 'none'})"
            )
            
            return list(tasks)
            
        except Exception as e:
            logger.error(f"Error retrieving tasks for {equipment_id}: {str(e)}")
            return []
    
    async def complete_task(
        self,
        task_id: str,
        actual_duration_hours: Optional[int] = None,
        actual_cost: Optional[float] = None,
        completion_notes: Optional[str] = None
    ) -> Optional[MaintenanceTaskDB]:
        """
        Mark task as completed.
        
        Args:
            task_id: Task UUID
            actual_duration_hours: Actual time taken
            actual_cost: Actual cost incurred
            completion_notes: Notes about completion
        
        Returns:
            Updated MaintenanceTaskDB object or None if not found
        """
        task = await self.get_task_by_id(task_id)
        
        if not task:
            logger.warning(f"Cannot complete task: {task_id} not found")
            return None
        
        try:
            task.status = "COMPLETED"
            task.completed_date = datetime.utcnow()
            task.actual_duration_hours = actual_duration_hours
            task.actual_cost = actual_cost
            task.completion_notes = completion_notes
            task.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"Task completed: {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {str(e)}")
            await self.db.rollback()
            return None
