"""
Dashboard Service - FastAPI Application.

Port: 8004
Purpose: Data aggregation and visualization for DRDO equipment monitoring.
"""

import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .config import settings
from .database import get_db, close_db
from .models import DashboardSummary, EquipmentOverview, EquipmentDetail, HealthResponse
from .services import dashboard_service

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
    
    Handles initialization and graceful shutdown.
    """
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")
    try:
        await dashboard_service.init_redis()
        await dashboard_service.init_http_client()
        logger.info(f"{settings.SERVICE_NAME} started successfully on port {settings.PORT}")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    try:
        await dashboard_service.close_http_client()
        await dashboard_service.close_redis()
        await close_db()
        logger.info(f"{settings.SERVICE_NAME} shut down successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="DRDO Dashboard Service",
    description="Microservice for data aggregation and visualization",
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
    """Readiness check endpoint with database and upstream services."""
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
        if dashboard_service.redis_client:
            await dashboard_service.redis_client.ping()
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
@app.get(
    "/api/v1/dashboard/summary",
    response_model=DashboardSummary,
    tags=["Dashboard"]
)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard summary with system-wide statistics.
    
    Returns aggregated data from all services including equipment count,
    alerts, maintenance schedules, and health metrics.
    """
    try:
        summary = await dashboard_service.get_dashboard_summary(db)
        return summary
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard summary"
        )


@app.get(
    "/api/v1/dashboard/equipment",
    response_model=list[EquipmentOverview],
    tags=["Dashboard"]
)
async def get_equipment_overview(db: AsyncSession = Depends(get_db)):
    """
    Get overview of all equipment.
    
    Returns list of all equipment with health scores, alerts, and maintenance status.
    """
    try:
        equipment = await dashboard_service.get_equipment_overview(db)
        return equipment
    except Exception as e:
        logger.error(f"Failed to get equipment overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve equipment overview"
        )


@app.get(
    "/api/v1/dashboard/equipment/{equipment_id}",
    response_model=EquipmentDetail,
    tags=["Dashboard"]
)
async def get_equipment_detail(
    equipment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information for specific equipment.
    
    Returns comprehensive data including sensor readings, predictions,
    alerts, maintenance schedule, and trend data.
    """
    try:
        detail = await dashboard_service.get_equipment_detail(equipment_id, db)
        
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment not found: {equipment_id}"
            )
        
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get equipment detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve equipment detail"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
