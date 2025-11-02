"""
Sensor Data Ingestion Service - FastAPI Application.

Port: 8001
Purpose: Data collection, validation, and storage for DRDO equipment sensors.
"""

import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from .config import settings
from .database import get_db, init_db, close_db
from .models import SensorReading, SensorReadingResponse, HealthResponse, ErrorResponse
from .services import sensor_service

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
        await sensor_service.init_redis()
        logger.info(f"{settings.SERVICE_NAME} started successfully on port {settings.PORT}")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    try:
        await sensor_service.close_redis()
        await close_db()
        logger.info(f"{settings.SERVICE_NAME} shut down successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="DRDO Sensor Data Ingestion Service",
    description="Microservice for collecting and storing equipment sensor data",
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
    """
    Basic health check endpoint.
    
    Returns service status without checking dependencies.
    """
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow()
    )


@app.get("/health/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check endpoint with database and Redis connectivity.
    
    Returns 200 if service is ready, 503 if not.
    """
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
        if sensor_service.redis_client:
            await sensor_service.redis_client.ping()
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
    "/api/v1/sensors/ingest",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensor Data"]
)
async def ingest_sensor_data(
    reading: SensorReading,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest sensor data from equipment.
    
    Validates, stores, and publishes sensor readings to downstream services.
    
    Args:
        reading: Sensor reading data with all measurements
        db: Database session (injected)
        
    Returns:
        SensorReadingResponse with reading ID and timestamp
        
    Raises:
        HTTPException: If ingestion fails
    """
    try:
        result = await sensor_service.ingest_sensor_data(reading, db)
        logger.info(f"Successfully ingested data for equipment: {reading.equipment_id}")
        return result
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest sensor data"
        )


@app.get(
    "/api/v1/sensors/{equipment_id}/latest",
    tags=["Sensor Data"]
)
async def get_latest_sensor_data(
    equipment_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve latest sensor readings for specific equipment.
    
    Args:
        equipment_id: Equipment identifier
        limit: Maximum number of readings to return (default: 10)
        db: Database session (injected)
        
    Returns:
        List of sensor readings ordered by timestamp (newest first)
    """
    try:
        equipment_id = equipment_id.upper()
        readings = await sensor_service.get_latest_readings(equipment_id, limit, db)
        
        return {
            "equipment_id": equipment_id,
            "count": len(readings),
            "readings": [
                {
                    "id": r.id,
                    "timestamp": r.timestamp,
                    "temperature": r.temperature,
                    "vibration": r.vibration,
                    "pressure": r.pressure,
                    "humidity": r.humidity,
                    "voltage": r.voltage,
                }
                for r in readings
            ]
        }
    except Exception as e:
        logger.error(f"Failed to retrieve readings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sensor data"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
