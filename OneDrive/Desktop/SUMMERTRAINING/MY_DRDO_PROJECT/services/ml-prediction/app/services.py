"""
Business logic layer for ML prediction service.

Handles prediction orchestration, validation, and response formatting.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .models import (
    SensorReadingInput,
    SensorData,
    SimplePredictionResponse,
    PredictionResponse,
    EquipmentHealthResponse,
)
from .ml_model import ModelInferenceService, get_model_service

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service layer for ML predictions.
    
    Handles business logic for failure predictions, equipment health monitoring,
    and response formatting.
    """
    
    def __init__(self, model_service: ModelInferenceService):
        """
        Initialize prediction service.
        
        Args:
            model_service: Initialized ModelInferenceService instance
        """
        self.model_service = model_service
        logger.info("PredictionService initialized")
    
    async def predict_equipment_failure(
        self,
        sensor_data: SensorReadingInput,
        equipment_id: str = "unknown"
    ) -> SimplePredictionResponse:
        """
        Predict equipment failure using ML model.
        
        Args:
            sensor_data: Sensor readings from equipment
            equipment_id: Equipment identifier for logging
        
        Returns:
            SimplePredictionResponse with prediction results
            
        Raises:
            ValueError: If sensor data is invalid
            RuntimeError: If model prediction fails
        """
        logger.info(f"Processing prediction request for equipment: {equipment_id}")
        logger.debug(f"Sensor data: {sensor_data.model_dump()}")
        
        try:
            # Convert Pydantic model to dict for ML model
            sensor_dict = sensor_data.model_dump()
            
            # Make prediction using ML model
            prediction_result = self.model_service.predict_failure(
                sensor_data=sensor_dict,
                equipment_id=equipment_id
            )
            
            # Format response
            response = SimplePredictionResponse(
                failure_probability=prediction_result["failure_probability"],
                severity=prediction_result["severity"],
                days_until_failure=prediction_result["days_until_failure"],
                health_score=prediction_result["health_score"],
                confidence=prediction_result["confidence"],
                recommended_action=prediction_result["recommended_action"],
                timestamp=datetime.utcnow()
            )
            
            logger.info(
                f"Prediction completed for {equipment_id}: "
                f"severity={response.severity}, "
                f"health_score={response.health_score:.1f}"
            )
            
            return response
            
        except KeyError as e:
            error_msg = f"Missing required sensor reading: {str(e)}"
            logger.error(f"Prediction failed for {equipment_id}: {error_msg}")
            raise ValueError(error_msg)
            
        except ValueError as e:
            error_msg = f"Invalid sensor data: {str(e)}"
            logger.error(f"Prediction failed for {equipment_id}: {error_msg}")
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"Prediction failed: {str(e)}"
            logger.error(f"Unexpected error for {equipment_id}: {error_msg}", exc_info=True)
            raise RuntimeError(error_msg)
    
    async def predict_with_equipment_id(
        self,
        sensor_data: SensorData
    ) -> PredictionResponse:
        """
        Predict equipment failure with equipment ID tracking.
        
        Args:
            sensor_data: Sensor readings with equipment ID
        
        Returns:
            PredictionResponse with equipment ID and prediction results
            
        Raises:
            ValueError: If sensor data is invalid
            RuntimeError: If model prediction fails
        """
        logger.info(f"Processing prediction request for equipment: {sensor_data.equipment_id}")
        
        try:
            # Extract sensor readings (exclude equipment_id)
            sensor_dict = {
                "temperature": sensor_data.temperature,
                "vibration": sensor_data.vibration,
                "pressure": sensor_data.pressure,
                "humidity": sensor_data.humidity,
                "voltage": sensor_data.voltage
            }
            
            # Make prediction
            prediction_result = self.model_service.predict_failure(
                sensor_data=sensor_dict,
                equipment_id=sensor_data.equipment_id
            )
            
            # Format response with equipment ID
            response = PredictionResponse(
                equipment_id=sensor_data.equipment_id,
                prediction=prediction_result["prediction"],
                failure_probability=prediction_result["failure_probability"],
                severity=prediction_result["severity"],
                days_until_failure=prediction_result["days_until_failure"],
                confidence=prediction_result["confidence"],
                timestamp=datetime.utcnow(),
                model_version=prediction_result.get("model_version", "unknown")
            )
            
            logger.info(
                f"Prediction completed for {sensor_data.equipment_id}: "
                f"severity={response.severity}, "
                f"probability={response.failure_probability:.3f}"
            )
            
            return response
            
        except (KeyError, ValueError) as e:
            logger.error(f"Prediction failed for {sensor_data.equipment_id}: {str(e)}")
            raise ValueError(str(e))
            
        except Exception as e:
            logger.error(
                f"Unexpected error for {sensor_data.equipment_id}: {str(e)}",
                exc_info=True
            )
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    async def get_equipment_health(
        self,
        equipment_id: str
    ) -> EquipmentHealthResponse:
        """
        Get current health status of equipment.
        
        NOTE: This is a placeholder implementation. In production, this would:
        1. Fetch latest sensor readings from sensor-ingestion-service
        2. Make prediction based on latest data
        3. Return comprehensive health status
        
        For now, returns mock data.
        
        Args:
            equipment_id: Equipment identifier
        
        Returns:
            EquipmentHealthResponse with health status
            
        Raises:
            ValueError: If equipment_id is invalid
            RuntimeError: If health data cannot be retrieved
        """
        logger.info(f"Fetching health status for equipment: {equipment_id}")
        
        # Validate equipment ID format
        if not self._validate_equipment_id(equipment_id):
            raise ValueError(
                f"Invalid equipment ID format: {equipment_id}. "
                f"Expected format: TYPE-LOCATION-NUMBER (e.g., RADAR-LOC-001)"
            )
        
        try:
            # TODO: In production, integrate with sensor-ingestion-service
            # For now, return mock healthy status
            
            # Calculate next maintenance date (30 days from now for healthy equipment)
            next_maintenance = datetime.utcnow() + timedelta(days=30)
            
            # Mock healthy equipment data
            response = EquipmentHealthResponse(
                equipment_id=equipment_id,
                health_score=85.0,
                status="HEALTHY",
                last_check=datetime.utcnow(),
                next_maintenance=next_maintenance,
                failure_probability=0.15
            )
            
            logger.info(
                f"Health status retrieved for {equipment_id}: "
                f"status={response.status}, "
                f"health_score={response.health_score:.1f}"
            )
            logger.warning(
                f"Using mock health data for {equipment_id}. "
                f"Integrate with sensor-ingestion-service for real data."
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Failed to retrieve health status: {str(e)}"
            logger.error(f"Health check failed for {equipment_id}: {error_msg}", exc_info=True)
            raise RuntimeError(error_msg)
    
    def _validate_equipment_id(self, equipment_id: str) -> bool:
        """
        Validate equipment ID format.
        
        DRDO equipment IDs follow pattern: TYPE-LOCATION-NUMBER
        Example: RADAR-LOC-001, AIRCRAFT-BASE-042
        
        Args:
            equipment_id: Equipment identifier to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not equipment_id or not isinstance(equipment_id, str):
            return False
        
        # Pattern: UPPERCASE-ALPHANUMERIC-DIGITS
        pattern = r'^[A-Z]+-[A-Z0-9]+-\d{3}$'
        return bool(re.match(pattern, equipment_id))
    
    def _calculate_status(self, health_score: float) -> str:
        """
        Calculate overall status from health score.
        
        Args:
            health_score: Health score (0-100)
        
        Returns:
            Status string (HEALTHY/WARNING/CRITICAL)
        """
        if health_score >= 70.0:
            return "HEALTHY"
        elif health_score >= 40.0:
            return "WARNING"
        else:
            return "CRITICAL"
    
    async def batch_predict(
        self,
        sensor_readings: List[SensorData]
    ) -> List[PredictionResponse]:
        """
        Make predictions for multiple equipment readings.
        
        Args:
            sensor_readings: List of sensor data with equipment IDs
        
        Returns:
            List of prediction responses
            
        Raises:
            ValueError: If input is invalid
        """
        logger.info(f"Processing batch prediction for {len(sensor_readings)} readings")
        
        if not sensor_readings:
            raise ValueError("No sensor readings provided")
        
        if len(sensor_readings) > 100:
            raise ValueError(f"Too many readings ({len(sensor_readings)}). Maximum is 100.")
        
        results = []
        failed_count = 0
        
        for idx, reading in enumerate(sensor_readings):
            try:
                prediction = await self.predict_with_equipment_id(reading)
                results.append(prediction)
            except Exception as e:
                logger.error(
                    f"Prediction failed for reading {idx+1} "
                    f"(equipment: {reading.equipment_id}): {str(e)}"
                )
                failed_count += 1
                # Continue processing remaining readings
        
        logger.info(
            f"Batch prediction completed: "
            f"{len(results)} successful, {failed_count} failed"
        )
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service health status.
        
        Returns:
            Dictionary with service status information
        """
        model_health = self.model_service.health_check()
        
        return {
            "service": "ml-prediction-service",
            "status": "healthy" if model_health["status"] == "healthy" else "unhealthy",
            "model_loaded": model_health["model_loaded"],
            "model_version": model_health.get("model_version", "unknown"),
            "timestamp": datetime.utcnow()
        }


# Global service instance (will be initialized in main.py)
_prediction_service: Optional[PredictionService] = None


def get_prediction_service() -> PredictionService:
    """
    Get the global PredictionService instance.
    
    Returns:
        PredictionService instance
        
    Raises:
        RuntimeError: If service is not initialized
    """
    if _prediction_service is None:
        raise RuntimeError(
            "PredictionService not initialized. "
            "Call initialize_service() first."
        )
    return _prediction_service


def initialize_service(model_service: ModelInferenceService) -> PredictionService:
    """
    Initialize the global PredictionService instance.
    
    Args:
        model_service: Initialized ModelInferenceService
    
    Returns:
        Initialized PredictionService instance
    """
    global _prediction_service
    _prediction_service = PredictionService(model_service)
    logger.info("Global PredictionService initialized")
    return _prediction_service
