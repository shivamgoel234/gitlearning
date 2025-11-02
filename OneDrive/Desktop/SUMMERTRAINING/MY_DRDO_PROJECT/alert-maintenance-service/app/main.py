"""
Alert & Maintenance Service - FastAPI Application.

Port: 8003
Purpose: Alert generation and maintenance scheduling for DRDO equipment.
"""

import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from .config import settings
from .database import get_db, init_db, close_db, AlertDB, MaintenanceScheduleDB
from .models import (
    AlertRequest, AlertResponse, AcknowledgeAlertRequest,
    MaintenanceScheduleRequest, MaintenanceScheduleResponse,
    HealthResponse, ErrorResponse
)
from .services import alert_service

# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": settings.SERVICE_NAME,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# Setup logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles database initialization and graceful shutdown.
    """
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")
    try:
        await init_db()
        await alert_service.init_redis()
        logger.info(f"{settings.SERVICE_NAME} started successfully on port {settings.PORT}")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    try:
        await alert_service.close_redis()
        await close_db()
        logger.info(f"{settings.SERVICE_NAME} shut down successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="DRDO Alert & Maintenance Service",
    description="Microservice for alert generation and maintenance scheduling",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow()
    )


@app.get("/health/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check endpoint with database and Redis connectivity."""
    db_status = "unknown"
    redis_status = "unknown"
    
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    # Check Redis connectivity
    try:
        if alert_service.redis_client:
            await alert_service.redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "not_initialized"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "disconnected"
    
    is_ready = (db_status == "connected" and redis_status == "connected")
    
    response = HealthResponse(
        status="ready" if is_ready else "not_ready",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow(),
        database=db_status,
        redis=redis_status
    )
    
    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump()
        )
    
    return response


# API endpoints
@app.post(
    "/api/v1/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Alerts"]
)
async def create_alert(
    request: AlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create new alert based on prediction."""
    try:
        result = await alert_service.create_alert(
            equipment_id=request.equipment_id,
            prediction_id=request.prediction_id,
            severity=request.severity,
            failure_probability=request.failure_probability,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


@app.get("/api/v1/alerts/{equipment_id}", tags=["Alerts"])
async def get_equipment_alerts(
    equipment_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get alerts for specific equipment."""
    try:
        equipment_id = equipment_id.upper()
        
        stmt = select(AlertDB).where(
            AlertDB.equipment_id == equipment_id
        ).order_by(AlertDB.timestamp.desc()).limit(limit)
        
        result = await db.execute(stmt)
        alerts = result.scalars().all()
        
        return {
            "equipment_id": equipment_id,
            "count": len(alerts),
            "alerts": [
                {
                    "alert_id": a.id,
                    "severity": a.severity,
                    "message": a.message,
                    "failure_probability": a.failure_probability,
                    "acknowledged": a.acknowledged,
                    "timestamp": a.timestamp
                }
                for a in alerts
            ]
        }
    except Exception as e:
        logger.error(f"Failed to retrieve alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@app.post("/api/v1/alerts/{alert_id}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert."""
    try:
        success = await alert_service.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=request.acknowledged_by,
            notes=request.notes,
            db=db
        )
        return {"acknowledged": success, "alert_id": alert_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@app.post(
    "/api/v1/maintenance/schedule",
    response_model=MaintenanceScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Maintenance"]
)
async def schedule_maintenance(
    request: MaintenanceScheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """Schedule maintenance for equipment."""
    try:
        result = await alert_service.schedule_maintenance(
            equipment_id=request.equipment_id,
            alert_id=None,
            scheduled_date=request.scheduled_date,
            priority=request.priority,
            task_type=request.task_type,
            description=request.description,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Failed to schedule maintenance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule maintenance"
        )


@app.get("/api/v1/maintenance/{equipment_id}", tags=["Maintenance"])
async def get_maintenance_schedules(
    equipment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get maintenance schedules for equipment."""
    try:
        equipment_id = equipment_id.upper()
        
        stmt = select(MaintenanceScheduleDB).where(
            MaintenanceScheduleDB.equipment_id == equipment_id
        ).order_by(MaintenanceScheduleDB.scheduled_date)
        
        result = await db.execute(stmt)
        schedules = result.scalars().all()
        
        return {
            "equipment_id": equipment_id,
            "count": len(schedules),
            "schedules": [
                {
                    "schedule_id": s.id,
                    "scheduled_date": s.scheduled_date,
                    "priority": s.priority,
                    "task_type": s.task_type,
                    "description": s.description,
                    "status": s.status,
                    "completed": s.completed
                }
                for s in schedules
            ]
        }
    except Exception as e:
        logger.error(f"Failed to retrieve schedules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedules"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
