"""
Main FastAPI application for Sensor Ingestion Service.

Implements all endpoints, error handling, middleware, and lifecycle management.
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis_async
from contextlib import asynccontextmanager
from datetime import datetime
import time
import logging

from .config import settings
from .models import (
    SensorReading,
    SensorReadingResponse,
    SensorReadingBatch,
    SensorReadingBatchResponse,
    ErrorResponse,
    HealthCheckResponse,
    ReadinessCheckResponse,
    LatestReadingsResponse
)
from .services import SensorIngestionService
from .database import get_db, init_db_engine, init_db_tables, close_db_engine, check_db_connection
from .dependencies import get_redis, init_redis, close_redis, check_redis_connection
from .middleware import RequestIDMiddleware, RequestLoggingMiddleware
from .exceptions import SensorIngestionException
from .logger import setup_logging, get_logger

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Track startup time for uptime calculation
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 80)
    
    try:
        # Initialize database
        await init_db_engine()
        await init_db_tables()
        
        # Initialize Redis
        await init_redis()
        
        logger.info(f"{settings.SERVICE_NAME} started successfully")
        logger.info(f"API documentation available at http://{settings.HOST}:{settings.PORT}/docs")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    
    try:
        await close_redis()
        await close_db_engine()
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="Sensor Data Ingestion Service for DRDO Equipment Maintenance",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(SensorIngestionException)
async def sensor_ingestion_exception_handler(
    request: Request,
    exc: SensorIngestionException
) -> JSONResponse:
    """Handle custom sensor ingestion exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            detail=exc.message,
            status_code=exc.status_code,
            timestamp=datetime.utcnow(),
            request_id=request_id
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            detail=str(exc),
            status_code=422,
            timestamp=datetime.utcnow(),
            request_id=request_id
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            detail="An unexpected error occurred",
            status_code=500,
            timestamp=datetime.utcnow(),
            request_id=request_id
        ).model_dump()
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """
    Kubernetes liveness probe endpoint.
    
    Returns service health status including database and Redis connectivity.
    """
    db_status = await check_db_connection()
    redis_status = await check_redis_connection()
    
    overall_status = "healthy" if (db_status and redis_status) else "unhealthy"
    
    return HealthCheckResponse(
        service=settings.SERVICE_NAME,
        status=overall_status,
        version=settings.SERVICE_VERSION,
        timestamp=datetime.utcnow(),
        database="connected" if db_status else "disconnected",
        redis="connected" if redis_status else "disconnected",
        uptime_seconds=time.time() - startup_time
    )


@app.get("/health/ready", response_model=ReadinessCheckResponse, tags=["Health"])
async def readiness_check() -> ReadinessCheckResponse:
    """
    Kubernetes readiness probe endpoint.
    
    Returns whether service is ready to accept traffic.
    """
    db_status = await check_db_connection()
    redis_status = await check_redis_connection()
    
    checks = {
        "database": "ready" if db_status else "not_ready",
        "redis": "ready" if redis_status else "not_ready"
    }
    
    ready = db_status and redis_status
    
    return ReadinessCheckResponse(
        ready=ready,
        checks=checks
    )


# ============================================================================
# SENSOR DATA INGESTION ENDPOINTS
# ============================================================================

@app.post(
    f"{settings.API_V1_PREFIX}/sensors/ingest",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensor Data"]
)
async def ingest_sensor_data(
    reading: SensorReading,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: redis_async.Redis = Depends(get_redis)
) -> SensorReadingResponse:
    """
    Ingest single sensor reading.
    
    Validates sensor data, stores in database, and publishes to Redis queue
    for ML prediction service to consume.
    
    - **equipment_id**: Equipment identifier (format: TYPE-LOCATION-NNN)
    - **temperature**: Temperature in Celsius (-50 to 200)
    - **vibration**: Vibration level in mm/s (0 to 2.0)
    - **pressure**: Pressure in bar (0 to 10.0)
    - **humidity**: Optional humidity percentage (0 to 100)
    - **voltage**: Optional voltage in volts (0 to 500)
    - **timestamp**: Optional UTC timestamp (defaults to current time)
    """
    request_id = getattr(request.state, "request_id", None)
    
    service = SensorIngestionService(db, redis)
    response = await service.ingest_sensor_data(reading, request_id)
    
    return response


@app.post(
    f"{settings.API_V1_PREFIX}/sensors/ingest/batch",
    response_model=SensorReadingBatchResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensor Data"]
)
async def ingest_sensor_data_batch(
    batch: SensorReadingBatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: redis_async.Redis = Depends(get_redis)
) -> SensorReadingBatchResponse:
    """
    Ingest batch of sensor readings.
    
    Processes multiple readings in a single request (max 100 per batch).
    Continues processing on individual failures.
    
    Returns summary with successful count, failed count, and error details.
    """
    request_id = getattr(request.state, "request_id", None)
    
    service = SensorIngestionService(db, redis)
    response = await service.ingest_batch(batch.readings, request_id)
    
    return response


@app.get(
    f"{settings.API_V1_PREFIX}/sensors/{{equipment_id}}/latest",
    response_model=LatestReadingsResponse,
    tags=["Sensor Data"]
)
async def get_latest_readings(
    equipment_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    redis: redis_async.Redis = Depends(get_redis)
) -> LatestReadingsResponse:
    """
    Retrieve latest sensor readings for equipment.
    
    - **equipment_id**: Equipment identifier
    - **limit**: Maximum number of readings to return (default: 10, max: 100)
    """
    if limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 100"
        )
    
    service = SensorIngestionService(db, redis)
    readings = await service.get_latest_readings(equipment_id, limit)
    
    return LatestReadingsResponse(
        equipment_id=equipment_id,
        count=len(readings),
        readings=readings
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": f"/docs",
        "health": "/health",
        "api_prefix": settings.API_V1_PREFIX
    }


# For local development
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
