"""
Business logic for ML Prediction Service.

Handles ML model loading, inference, and prediction storage.
"""

import uuid
import json
import logging
import numpy as np
from datetime import datetime
from typing import Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from .models import PredictionRequest, PredictionResponse
from .database import PredictionDB
from .config import settings

logger = logging.getLogger(__name__)


class MLPredictionService:
    """Service class for ML prediction operations."""
    
    def __init__(self):
        """Initialize service with model and Redis connection."""
        self.model: Optional[any] = None
        self.model_metadata: Optional[dict] = None
        self.redis_client: Optional[redis.Redis] = None
    
    def load_model(self) -> None:
        """
        Load ML model from disk.
        
        Loads both the model file and metadata for inference.
        
        Raises:
            FileNotFoundError: If model files not found
            Exception: If model loading fails
        """
        try:
            # For now, use a mock model since we don't have trained model yet
            # In production, uncomment the joblib loading:
            # import joblib
            # self.model = joblib.load(settings.MODEL_PATH)
            
            logger.warning("Using mock model - replace with trained model in production")
            self.model = MockModel()
            
            # Load model metadata
            metadata_path = Path(settings.MODEL_METADATA_PATH)
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.model_metadata = json.load(f)
                logger.info(f"Model metadata loaded: version {self.model_metadata.get('version', 'unknown')}")
            else:
                self.model_metadata = {"version": "1.0", "type": "mock"}
                logger.warning("Model metadata not found, using defaults")
            
            logger.info("ML model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
    
    async def init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}", exc_info=True)
            raise
    
    async def close_redis(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def predict_failure(
        self,
        request: PredictionRequest,
        db: AsyncSession
    ) -> PredictionResponse:
        """
        Predict equipment failure probability.
        
        Args:
            request: Prediction request with sensor data
            db: Database session
            
        Returns:
            PredictionResponse with failure probability and severity
            
        Raises:
            ValueError: If model not loaded
            Exception: If prediction fails
        """
        if not self.model:
            raise ValueError("ML model not loaded")
        
        try:
            # Prepare features for model
            features = np.array([[
                request.temperature,
                request.vibration,
                request.pressure,
                request.humidity or 0.0,
                request.voltage or 0.0
            ]])
            
            # Get prediction from model
            failure_prob = float(self.model.predict_proba(features)[0][1])
            
            # Calculate severity and days until failure
            severity, days_until_failure = self._calculate_severity(failure_prob)
            
            # Calculate health score
            health_score = self._calculate_health_score(
                request.temperature,
                request.vibration,
                request.pressure,
                failure_prob
            )
            
            # Determine confidence
            confidence = self._calculate_confidence(failure_prob)
            
            # Generate prediction ID
            prediction_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Save prediction to database
            db_prediction = PredictionDB(
                id=prediction_id,
                equipment_id=request.equipment_id,
                timestamp=timestamp,
                failure_probability=failure_prob,
                severity=severity,
                health_score=health_score,
                days_until_failure=days_until_failure,
                confidence=confidence,
                temperature=request.temperature,
                vibration=request.vibration,
                pressure=request.pressure,
                humidity=request.humidity,
                voltage=request.voltage,
                model_version=self.model_metadata.get("version", "unknown")
            )
            
            db.add(db_prediction)
            await db.commit()
            await db.refresh(db_prediction)
            
            logger.info(
                f"Prediction generated: equipment_id={request.equipment_id}, "
                f"failure_prob={failure_prob:.3f}, severity={severity}"
            )
            
            # Publish prediction event to Redis
            await self._publish_prediction_event(prediction_id, request.equipment_id, failure_prob, severity)
            
            return PredictionResponse(
                prediction_id=prediction_id,
                equipment_id=request.equipment_id,
                failure_probability=round(failure_prob, 3),
                severity=severity,
                health_score=round(health_score, 1),
                days_until_failure=days_until_failure,
                confidence=confidence,
                timestamp=timestamp
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise
    
    def _calculate_severity(self, failure_prob: float) -> tuple[str, int]:
        """
        Calculate severity level based on failure probability.
        
        Args:
            failure_prob: Failure probability (0-1)
            
        Returns:
            Tuple of (severity_level, days_until_failure)
        """
        if failure_prob >= settings.CRITICAL_THRESHOLD:
            return "CRITICAL", 7
        elif failure_prob >= settings.HIGH_THRESHOLD:
            return "HIGH", 15
        elif failure_prob >= settings.MEDIUM_THRESHOLD:
            return "MEDIUM", 30
        else:
            return "LOW", 60
    
    def _calculate_health_score(
        self,
        temperature: float,
        vibration: float,
        pressure: float,
        failure_prob: float
    ) -> float:
        """
        Calculate equipment health score (0-100).
        
        Higher score means better health.
        
        Args:
            temperature: Temperature reading
            vibration: Vibration reading
            pressure: Pressure reading
            failure_prob: Failure probability
            
        Returns:
            Health score between 0.0 and 100.0
        """
        # Invert failure probability to health score
        base_score = (1.0 - failure_prob) * 100
        
        # Adjust based on sensor readings (simplified logic)
        temp_penalty = max(0, (temperature - 100) / 100 * 10)
        vibration_penalty = (vibration / 2.0) * 5
        pressure_penalty = max(0, (pressure - 5) / 5 * 5)
        
        health_score = base_score - temp_penalty - vibration_penalty - pressure_penalty
        
        return max(0.0, min(100.0, health_score))
    
    def _calculate_confidence(self, failure_prob: float) -> str:
        """
        Calculate prediction confidence level.
        
        Args:
            failure_prob: Failure probability
            
        Returns:
            Confidence level (high/medium/low)
        """
        if failure_prob > 0.7 or failure_prob < 0.3:
            return "high"
        elif failure_prob > 0.5 or failure_prob < 0.5:
            return "medium"
        else:
            return "low"
    
    async def _publish_prediction_event(
        self,
        prediction_id: str,
        equipment_id: str,
        failure_prob: float,
        severity: str
    ) -> None:
        """
        Publish prediction event to Redis pub/sub.
        
        Args:
            prediction_id: Unique prediction identifier
            equipment_id: Equipment identifier
            failure_prob: Failure probability
            severity: Severity level
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized, skipping event publish")
            return
        
        try:
            event_data = {
                "event_type": "prediction_generated",
                "prediction_id": prediction_id,
                "equipment_id": equipment_id,
                "failure_probability": failure_prob,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(
                "prediction_channel",
                json.dumps(event_data)
            )
            
            logger.debug(f"Published prediction event for equipment_id={equipment_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish prediction event: {e}", exc_info=True)


class MockModel:
    """Mock ML model for development/testing."""
    
    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """
        Generate mock prediction probabilities.
        
        Args:
            features: Input features array
            
        Returns:
            Array of prediction probabilities [no_failure, failure]
        """
        # Simple heuristic based on temperature and vibration
        temp, vibration, pressure, humidity, voltage = features[0]
        
        # Calculate failure probability based on sensor readings
        temp_factor = max(0, (temp - 80) / 120)
        vibration_factor = vibration / 2.0
        pressure_factor = max(0, (pressure - 5) / 5)
        
        failure_prob = min(0.95, (temp_factor + vibration_factor + pressure_factor) / 3)
        
        return np.array([[1 - failure_prob, failure_prob]])


# Global service instance
ml_service = MLPredictionService()
