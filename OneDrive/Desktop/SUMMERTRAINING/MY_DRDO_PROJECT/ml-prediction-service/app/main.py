"""
ML Prediction Service - FastAPI Application.

Port: 8002
Purpose: ML inference and health scoring for DRDO equipment.
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

from .config import settings
from .database import get_db, init_db, close_db
from .models import (
    PredictionRequest, PredictionResponse, HealthScoreRequest,
    HealthScoreResponse, HealthResponse, ErrorResponse
)
from .services import ml_service

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
    
    Handles database initialization, model loading, and graceful shutdown.
    """
    # Startup
    logger.info(f"{settings.SERVICE_NAME} starting up...")
    try:
        await init_db()
        ml_service.load_model()
        await ml_service.init_redis()
        logger.info(f"{settings.SERVICE_NAME} started successfully on port {settings.PORT}")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info(f"{settings.SERVICE_NAME} shutting down...")
    try:
        await ml_service.close_redis()
        await close_db()
        logger.info(f"{settings.SERVICE_NAME} shut down successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="DRDO ML Prediction Service",
    description="Microservice for equipment failure prediction and health scoring",
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
        timestamp=datetime.utcnow(),
        model_loaded=ml_service.model is not None
    )


@app.get("/health/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check endpoint with database, Redis, and model status.
    
    Returns 200 if service is ready, 503 if not.
    """
    db_status = "unknown"
    redis_status = "unknown"
    model_loaded = ml_service.model is not None
    
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    # Check Redis connectivity
    try:
        if ml_service.redis_client:
            await ml_service.redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "not_initialized"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "disconnected"
    
    is_ready = (db_status == "connected" and redis_status == "connected" and model_loaded)
    
    response = HealthResponse(
        status="ready" if is_ready else "not_ready",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow(),
        database=db_status,
        redis=redis_status,
        model_loaded=model_loaded
    )
    
    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump()
        )
    
    return response


# API endpoints
@app.post(
    "/api/v1/predict/failure",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Predictions"]
)
async def predict_equipment_failure(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict equipment failure probability.
    
    Analyzes sensor data and returns failure prediction with severity level.
    
    Args:
        request: Prediction request with sensor data
        db: Database session (injected)
        
    Returns:
        PredictionResponse with failure probability and health metrics
        
    Raises:
        HTTPException: If prediction fails
    """
    try:
        result = await ml_service.predict_failure(request, db)
        logger.info(
            f"Prediction completed: equipment_id={request.equipment_id}, "
            f"severity={result.severity}"
        )
        return result
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate prediction"
        )


@app.get(
    "/api/v1/health-score/{equipment_id}",
    response_model=HealthScoreResponse,
    tags=["Health Score"]
)
async def get_equipment_health_score(
    equipment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current health score for equipment.
    
    Returns the latest health score based on recent predictions.
    
    Args:
        equipment_id: Equipment identifier
        db: Database session (injected)
        
    Returns:
        HealthScoreResponse with current health metrics
    """
    try:
        equipment_id = equipment_id.upper()
        
        # Get latest prediction from database
        from sqlalchemy import select
        from .database import PredictionDB
        
        stmt = select(PredictionDB).where(
            PredictionDB.equipment_id == equipment_id
        ).order_by(PredictionDB.timestamp.desc()).limit(1)
        
        result = await db.execute(stmt)
        latest_prediction = result.scalar_one_or_none()
        
        if not latest_prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No predictions found for equipment {equipment_id}"
            )
        
        # Determine health status
        health_score = latest_prediction.health_score
        if health_score >= 90:
            health_status = "EXCELLENT"
        elif health_score >= 70:
            health_status = "GOOD"
        elif health_score >= 50:
            health_status = "FAIR"
        elif health_score >= 30:
            health_status = "POOR"
        else:
            health_status = "CRITICAL"
        
        return HealthScoreResponse(
            equipment_id=equipment_id,
            health_score=health_score,
            status=health_status,
            last_prediction=latest_prediction.timestamp,
            trend="stable"  # TODO: Calculate trend from historical data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve health score: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health score"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
