"""
Alert & Maintenance Service - FastAPI Application

Provides 4 core endpoints:
1. Health check
2. Generate alert (calls ML service)
3. Get active alerts
4. Schedule maintenance task
"""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import settings
from .database import get_db, init_db
from .models import AlertResponse, MaintenanceTaskCreate, MaintenanceTaskResponse
from .services import AlertGenerationService
from .schemas import AlertDB, MaintenanceTaskDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"alert-maintenance","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)


# ============================================================================
# APPLICATION LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Initialize database tables on startup
    - Cleanup resources on shutdown
    """
    # Startup
    logger.info("🚀 Starting Alert & Maintenance Service")
    try:
        await init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Alert & Maintenance Service")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Alert & Maintenance Service",
    version="1.0.0",
    description="Microservice for equipment failure alerts and maintenance scheduling",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# ============================================================================
# ENDPOINT 1: HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and timestamp.
    """
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "version": settings.SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# ENDPOINT 2: GENERATE ALERT (MAIN ENDPOINT)
# ============================================================================

@app.post(
    "/api/v1/alerts/generate",
    response_model=AlertResponse,
    status_code=201,
    summary="Generate alert for equipment",
    description="Sends sensor data to ML service, gets prediction, and creates alert if severity is HIGH or CRITICAL"
)
async def generate_alert(
    equipment_id: str = Query(..., description="Equipment identifier", example="RADAR-001"),
    temperature: float = Query(..., description="Temperature reading in Celsius", example=85.5),
    vibration: float = Query(..., description="Vibration level in mm/s", example=0.45),
    pressure: float = Query(..., description="Pressure reading in bar", example=3.2),
    humidity: float = Query(0.0, description="Humidity percentage (optional)", example=70.0),
    voltage: float = Query(0.0, description="Voltage reading (optional)", example=230.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate alert for equipment based on sensor readings.
    
    **Process:**
    1. Collect sensor data from query parameters
    2. Call ML Prediction service to get failure prediction
    3. If severity is HIGH or CRITICAL, create alert in database
    4. Queue email notification via Celery (async)
    5. Return created alert
    
    **Returns:**
    - 201: Alert created successfully
    - 404: No alert needed (severity LOW/MEDIUM)
    - 500: Internal server error
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=85.5&vibration=0.45&pressure=3.2"
    ```
    """
    logger.info(f"Generating alert for equipment: {equipment_id}")
    
    try:
        # Build sensor data dictionary
        sensor_data = {
            "temperature": temperature,
            "vibration": vibration,
            "pressure": pressure,
            "humidity": humidity,
            "voltage": voltage
        }
        
        logger.info(f"Sensor data: {sensor_data}")
        
        # Create alert service and generate alert
        alert_service = AlertGenerationService(db, settings.ML_PREDICTION_SERVICE_URL)
        alert = await alert_service.generate_alert_for_equipment(
            equipment_id,
            sensor_data
        )
        
        # Check if alert was created
        if not alert:
            logger.info(f"No alert created for {equipment_id} - severity below threshold")
            raise HTTPException(
                status_code=404,
                detail="No alert needed (severity LOW/MEDIUM - only HIGH/CRITICAL generate alerts)"
            )
        
        # Send email notification asynchronously via Celery
        try:
            from .tasks import send_email_alert
            
            alert_data = {
                "alert_id": alert.id,
                "equipment_id": alert.equipment_id,
                "severity": alert.severity,
                "failure_probability": alert.failure_probability,
                "days_until_failure": alert.days_until_failure,
                "recommended_action": alert.recommended_action
            }
            
            # Queue email task (non-blocking)
            send_email_alert.delay(alert_data)
            logger.info(f"✉️ Email notification queued for alert {alert.id}")
            
        except Exception as e:
            # Don't fail the request if email queuing fails
            logger.warning(f"Failed to queue email notification: {str(e)}")
        
        logger.info(f"✓ Alert generated successfully: {alert.id}")
        return AlertResponse.model_validate(alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating alert: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate alert: {str(e)}"
        )


# ============================================================================
# ENDPOINT 3: GET ACTIVE ALERTS
# ============================================================================

@app.get(
    "/api/v1/alerts/active",
    response_model=List[AlertResponse],
    summary="Get active alerts",
    description="Retrieve all active alerts with optional severity filter"
)
async def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    limit: int = Query(100, le=1000, description="Maximum number of alerts to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active alerts with optional filtering.
    
    **Query Parameters:**
    - `severity`: Filter by severity level (optional)
    - `limit`: Maximum number of results (default 100, max 1000)
    
    **Returns:**
    List of active alerts ordered by creation time (newest first)
    
    **Example:**
    ```bash
    # Get all active alerts
    curl "http://localhost:8003/api/v1/alerts/active"
    
    # Get only critical alerts
    curl "http://localhost:8003/api/v1/alerts/active?severity=CRITICAL"
    ```
    """
    logger.info(f"Retrieving active alerts (severity filter: {severity}, limit: {limit})")
    
    try:
        # Build query
        stmt = select(AlertDB).where(AlertDB.status == "ACTIVE")
        
        # Apply severity filter if provided
        if severity:
            severity_upper = severity.upper()
            if severity_upper not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid severity. Must be: CRITICAL, HIGH, MEDIUM, or LOW"
                )
            stmt = stmt.where(AlertDB.severity == severity_upper)
        
        # Order by creation time (newest first) and apply limit
        stmt = stmt.order_by(AlertDB.created_at.desc()).limit(limit)
        
        # Execute query
        result = await db.execute(stmt)
        alerts = result.scalars().all()
        
        logger.info(f"✓ Retrieved {len(alerts)} active alerts")
        
        # Convert to response models
        return [AlertResponse.model_validate(alert) for alert in alerts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )


# ============================================================================
# ENDPOINT 4: SCHEDULE MAINTENANCE
# ============================================================================

@app.post(
    "/api/v1/maintenance/schedule",
    response_model=MaintenanceTaskResponse,
    status_code=201,
    summary="Schedule maintenance task",
    description="Create a new maintenance task for equipment"
)
async def schedule_maintenance(
    request: MaintenanceTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a maintenance task for equipment.
    
    **Request Body:**
    - `equipment_id`: Equipment identifier (required)
    - `task_type`: ROUTINE, PREVENTIVE, CORRECTIVE, or EMERGENCY (required)
    - `priority`: LOW, MEDIUM, HIGH, or CRITICAL (required)
    - `scheduled_date`: When maintenance should be performed (required)
    - `title`: Task title (optional)
    - `description`: Detailed description (optional)
    - `estimated_duration_hours`: Estimated duration (optional)
    - `cost_estimate`: Estimated cost (optional)
    - `assigned_to`: User/team assignment (optional)
    - `alert_id`: Related alert ID (optional)
    
    **Returns:**
    - 201: Task created successfully
    - 422: Validation error
    - 500: Internal server error
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
      -H "Content-Type: application/json" \
      -d '{
        "equipment_id": "RADAR-001",
        "task_type": "PREVENTIVE",
        "priority": "HIGH",
        "scheduled_date": "2025-11-10T10:00:00Z",
        "title": "Cooling system maintenance",
        "estimated_duration_hours": 4,
        "cost_estimate": 5000.0
      }'
    ```
    """
    logger.info(f"Scheduling maintenance for equipment: {request.equipment_id}")
    
    try:
        # Create maintenance task
        task = MaintenanceTaskDB(
            id=str(uuid.uuid4()),
            equipment_id=request.equipment_id,
            task_type=request.task_type,
            priority=request.priority,
            scheduled_date=request.scheduled_date,
            status="SCHEDULED",
            title=request.title,
            description=request.description,
            estimated_duration_hours=request.estimated_duration_hours,
            cost_estimate=request.cost_estimate,
            assigned_to=request.assigned_to,
            notes=request.notes,
            alert_id=request.alert_id,
            parts_required=request.parts_required,
            source="manual",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        logger.info(
            f"✓ Maintenance task scheduled: {task.id} "
            f"(type: {task.task_type}, priority: {task.priority})"
        )
        
        return MaintenanceTaskResponse.model_validate(task)
        
    except Exception as e:
        logger.error(f"Error scheduling maintenance: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule maintenance: {str(e)}"
        )


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_message():
    """Log startup message with service information."""
    logger.info("=" * 60)
    logger.info(f"  {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info("=" * 60)
    logger.info(f"  Port: {settings.PORT}")
    logger.info(f"  ML Service: {settings.ML_PREDICTION_SERVICE_URL}")
    logger.info(f"  Database: {settings.DATABASE_URL.split('@')[-1]}")
    logger.info("=" * 60)
    logger.info("  Endpoints:")
    logger.info("    GET  /health")
    logger.info("    POST /api/v1/alerts/generate")
    logger.info("    GET  /api/v1/alerts/active")
    logger.info("    POST /api/v1/maintenance/schedule")
    logger.info("=" * 60)
