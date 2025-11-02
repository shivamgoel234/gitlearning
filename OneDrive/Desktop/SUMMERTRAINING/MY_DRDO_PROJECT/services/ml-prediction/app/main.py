"""
Main FastAPI application for ML Prediction Service.

Provides endpoints for equipment failure prediction using trained ML models.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from .config import settings
from .models import (
    SensorData,
    SensorReadingInput,
    SimplePredictionResponse,
    PredictionResponse,
    EquipmentHealthResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthCheckResponse,
    ModelInfoResponse,
    ErrorResponse
)
from .ml_model import get_model_service
from .services import initialize_service, get_prediction_service
from .utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Loads ML model on startup and handles cleanup on shutdown.
    """
    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info("=" * 80)
    
    try:
        # Initialize ML model service
        model_service = get_model_service()
        model_service.initialize()
        
        # Initialize prediction service
        prediction_service = initialize_service(model_service)
        
        # Store in app state
        app.state.model_service = model_service
        app.state.prediction_service = prediction_service
        
        logger.info(f"{settings.SERVICE_NAME} started successfully")
        logger.info(f"API documentation: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"Ready to serve predictions on port {settings.PORT}")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="ML Prediction Service for Equipment Failure Detection",
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


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            detail="An unexpected error occurred",
            status_code=500,
            timestamp=datetime.utcnow()
        ).model_dump()
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for Kubernetes liveness probe.
    
    Returns service health status and model loading status.
    """
    try:
        prediction_service = get_prediction_service()
        status_info = prediction_service.get_service_status()
        
        return HealthCheckResponse(
            service=settings.SERVICE_NAME,
            status=status_info["status"],
            version=settings.SERVICE_VERSION,
            model_loaded=status_info["model_loaded"],
            model_version=status_info.get("model_version"),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            service=settings.SERVICE_NAME,
            status="unhealthy",
            version=settings.SERVICE_VERSION,
            model_loaded=False,
            model_version=None,
            timestamp=datetime.utcnow()
        )


@app.get("/health/ready", response_model=HealthCheckResponse, tags=["Health"])
async def readiness_check() -> HealthCheckResponse:
    """
    Readiness check endpoint for Kubernetes readiness probe.
    
    Returns whether the service is ready to accept requests.
    """
    try:
        prediction_service = get_prediction_service()
        model_service = get_model_service()
        
        is_ready = model_service.is_loaded
        
        return HealthCheckResponse(
            service=settings.SERVICE_NAME,
            status="ready" if is_ready else "not_ready",
            version=settings.SERVICE_VERSION,
            model_loaded=is_ready,
            model_version=model_service.metadata.get("version", "unknown") if is_ready else None,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return HealthCheckResponse(
            service=settings.SERVICE_NAME,
            status="not_ready",
            version=settings.SERVICE_VERSION,
            model_loaded=False,
            model_version=None,
            timestamp=datetime.utcnow()
        )


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post(
    f"{settings.API_V1_PREFIX}/predict/failure",
    response_model=SimplePredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Predictions"],
    summary="Predict equipment failure",
    description="Predict equipment failure probability based on sensor readings"
)
async def predict_failure(sensor_data: SensorReadingInput) -> SimplePredictionResponse:
    """
    Predict equipment failure probability based on sensor readings.
    
    Returns comprehensive prediction results including:
    - **failure_probability**: Probability of failure (0-1)
    - **severity**: CRITICAL/HIGH/MEDIUM/LOW
    - **days_until_failure**: Estimated days before failure
    - **health_score**: Equipment health score (0-100)
    - **confidence**: Prediction confidence level (high/medium/low)
    - **recommended_action**: Maintenance recommendation
    
    **Example Request:**
    ```json
    {
      "temperature": 85.5,
      "vibration": 0.45,
      "pressure": 3.2,
      "humidity": 65.0,
      "voltage": 220.0
    }
    ```
    
    **Example Response:**
    ```json
    {
      "failure_probability": 0.82,
      "severity": "CRITICAL",
      "days_until_failure": 7,
      "health_score": 18.0,
      "confidence": "high",
      "recommended_action": "Schedule immediate maintenance - equipment likely to fail within 7 days",
      "timestamp": "2025-11-02T10:30:00Z"
    }
    ```
    """
    try:
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Make prediction
        prediction = await prediction_service.predict_equipment_failure(
            sensor_data=sensor_data,
            equipment_id="api_request"
        )
        
        logger.info(
            f"Prediction successful: severity={prediction.severity}, "
            f"health_score={prediction.health_score:.1f}"
        )
        
        return prediction
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Model inference error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post(
    f"{settings.API_V1_PREFIX}/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Predictions"],
    summary="Predict with equipment ID",
    description="Predict failure with equipment tracking"
)
async def predict_with_equipment(sensor_data: SensorData) -> PredictionResponse:
    """
    Predict equipment failure with equipment ID tracking.
    
    Makes a prediction using the loaded ML model and returns:
    - Binary prediction (0 = normal, 1 = failure likely)
    - Failure probability (0.0 to 1.0)
    - Severity level (CRITICAL, HIGH, MEDIUM, LOW)
    - Estimated days until failure
    - Confidence level
    - Equipment ID for tracking
    
    **Example Request:**
    ```json
    {
      "equipment_id": "RADAR-LOC-001",
      "temperature": 85.5,
      "vibration": 0.45,
      "pressure": 3.2,
      "humidity": 65.0,
      "voltage": 220.0
    }
    ```
    """
    try:
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Make prediction
        prediction = await prediction_service.predict_with_equipment_id(sensor_data)
        
        return prediction
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Model inference error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get(
    f"{settings.API_V1_PREFIX}/equipment/health/{{equipment_id}}",
    response_model=EquipmentHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Equipment"],
    summary="Get equipment health status",
    description="Retrieve current health status of specific equipment"
)
async def get_equipment_health(equipment_id: str) -> EquipmentHealthResponse:
    """
    Get current health status of specific equipment.
    
    Returns:
    - **equipment_id**: Equipment identifier
    - **health_score**: Current health score (0-100)
    - **status**: HEALTHY/WARNING/CRITICAL
    - **last_check**: Last health check timestamp
    - **next_maintenance**: Recommended next maintenance date
    - **failure_probability**: Current failure probability
    
    **Example:**
    ```
    GET /api/v1/equipment/health/RADAR-LOC-001
    ```
    
    **Note:** Currently returns mock data. In production, this would fetch
    latest sensor readings from sensor-ingestion-service.
    """
    try:
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Get equipment health
        health_status = await prediction_service.get_equipment_health(equipment_id)
        
        return health_status
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@app.post(
    f"{settings.API_V1_PREFIX}/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Predictions"],
    summary="Batch predictions",
    description="Make predictions for multiple equipment readings"
)
async def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """
    Make batch predictions for multiple equipment readings.
    
    Accepts up to 100 sensor readings and returns predictions for each.
    Failed predictions are logged but don't stop the batch process.
    
    **Example Request:**
    ```json
    {
      "readings": [
        {
          "equipment_id": "RADAR-LOC-001",
          "temperature": 85.5,
          "vibration": 0.45,
          "pressure": 3.2,
          "humidity": 65.0,
          "voltage": 220.0
        },
        {
          "equipment_id": "RADAR-LOC-002",
          "temperature": 78.2,
          "vibration": 0.38,
          "pressure": 3.0
        }
      ]
    }
    ```
    """
    try:
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Validate batch size
        if len(request.readings) > 100:
            raise ValueError(f"Too many readings ({len(request.readings)}). Maximum is 100.")
        
        # Make batch predictions
        predictions = await prediction_service.batch_predict(request.readings)
        
        logger.info(
            f"Batch prediction completed: {len(predictions)}/{len(request.readings)} successful"
        )
        
        return BatchPredictionResponse(
            predictions=predictions,
            total=len(predictions)
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


# ============================================================================
# MODEL INFO ENDPOINTS
# ============================================================================

@app.get(
    f"{settings.API_V1_PREFIX}/model/info",
    response_model=ModelInfoResponse,
    tags=["Model"],
    summary="Get model information",
    description="Retrieve detailed information about the loaded ML model"
)
async def get_model_info() -> ModelInfoResponse:
    """
    Get information about the loaded ML model.
    
    Returns comprehensive model metadata including:
    - **model_type**: Type of ML model (e.g., RandomForestClassifier)
    - **version**: Model version
    - **trained_date**: When the model was trained
    - **features**: List of input feature names
    - **accuracy**: Model accuracy on test set
    - **precision**: Model precision score
    - **recall**: Model recall score
    - **f1_score**: Model F1 score
    - **roc_auc**: Model ROC-AUC score
    
    **Example Response:**
    ```json
    {
      "model_type": "RandomForestClassifier",
      "version": "v1.0",
      "trained_date": "2025-10-15",
      "features": ["temperature", "vibration", "pressure", "humidity", "voltage"],
      "accuracy": 0.89,
      "precision": 0.87,
      "recall": 0.91,
      "f1_score": 0.89,
      "roc_auc": 0.93
    }
    ```
    """
    try:
        model_service = get_model_service()
        
        if not model_service.is_loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML model not loaded"
            )
        
        model_info = model_service.get_model_info()
        return ModelInfoResponse(**model_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
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
        "docs": "/docs",
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
