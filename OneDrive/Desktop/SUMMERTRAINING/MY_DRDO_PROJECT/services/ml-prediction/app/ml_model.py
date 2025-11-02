"""
ML model loading and inference module.

Handles loading trained ML models and making predictions with comprehensive
error handling, logging, and production-ready features.
"""

import joblib
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from .config import settings

logger = logging.getLogger(__name__)


class ModelInferenceService:
    """
    Production-ready service for loading and running ML model inference.
    
    This service implements singleton pattern for model loading, comprehensive
    error handling, and structured prediction results with severity classification.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        scaler_path: Optional[str] = None,
        feature_names_path: Optional[str] = None,
        metadata_path: Optional[str] = None
    ):
        """
        Initialize model inference service.
        
        Args:
            model_path: Path to trained Random Forest model (.pkl)
            scaler_path: Path to fitted StandardScaler (.pkl)
            feature_names_path: Path to feature names (.json)
            metadata_path: Path to model metadata (.json)
        """
        if self._initialized:
            return
            
        # Set paths (use settings if not provided)
        self.model_path = model_path or settings.MODEL_PATH
        self.scaler_path = scaler_path or settings.SCALER_PATH
        self.feature_names_path = feature_names_path or settings.FEATURE_NAMES_PATH
        self.metadata_path = metadata_path or getattr(settings, 'METADATA_PATH', None)
        
        # Model artifacts
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.metadata: Dict[str, Any] = {}
        
        # State tracking
        self.is_loaded: bool = False
        self._load_attempts: int = 0
        self._max_load_attempts: int = 3
        
        self._initialized = True
        logger.info("ModelInferenceService initialized (singleton)")
    
    def load_model(self) -> None:
        """
        Load Random Forest model from disk with error handling and retry logic.
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If loading fails after max attempts
        """
        self._load_attempts += 1
        
        if self._load_attempts > self._max_load_attempts:
            raise Exception(f"Failed to load model after {self._max_load_attempts} attempts")
        
        try:
            logger.info(f"Loading Random Forest model from {self.model_path} (attempt {self._load_attempts})")
            
            # Validate file exists
            model_file = Path(self.model_path)
            if not model_file.exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            # Load model
            self.model = joblib.load(self.model_path)
            
            # Validate model type
            if not hasattr(self.model, 'predict_proba'):
                raise ValueError("Loaded model doesn't support probability predictions")
            
            logger.info("✓ Random Forest model loaded successfully")
            logger.info(f"  Model type: {type(self.model).__name__}")
            logger.info(f"  Number of estimators: {getattr(self.model, 'n_estimators', 'unknown')}")
            logger.info(f"  Max depth: {getattr(self.model, 'max_depth', 'unknown')}")
            
        except FileNotFoundError as e:
            logger.error(f"Model file not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load model (attempt {self._load_attempts}): {str(e)}", exc_info=True)
            if self._load_attempts >= self._max_load_attempts:
                raise
    
    def load_scaler(self) -> None:
        """
        Load StandardScaler from disk.
        
        Raises:
            FileNotFoundError: If scaler file doesn't exist
            Exception: If loading fails
        """
        try:
            logger.info(f"Loading StandardScaler from {self.scaler_path}")
            
            # Validate file exists
            scaler_file = Path(self.scaler_path)
            if not scaler_file.exists():
                raise FileNotFoundError(f"Scaler file not found: {self.scaler_path}")
            
            # Load scaler
            self.scaler = joblib.load(self.scaler_path)
            
            # Validate scaler
            if not hasattr(self.scaler, 'transform'):
                raise ValueError("Loaded object is not a valid scaler")
            
            logger.info("✓ StandardScaler loaded successfully")
            logger.info(f"  Feature count: {len(getattr(self.scaler, 'feature_names_in_', []))}")
            logger.info(f"  Scale values: {getattr(self.scaler, 'scale_', 'unknown')}")
            
        except FileNotFoundError as e:
            logger.error(f"Scaler file not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load scaler: {str(e)}", exc_info=True)
            raise
    
    def load_feature_names(self) -> List[str]:
        """
        Load feature names from JSON file.
        
        Returns:
            List of feature names in training order
            
        Raises:
            FileNotFoundError: If feature names file doesn't exist
            Exception: If loading fails
        """
        try:
            logger.info(f"Loading feature names from {self.feature_names_path}")
            
            # Validate file exists
            names_file = Path(self.feature_names_path)
            if not names_file.exists():
                raise FileNotFoundError(f"Feature names file not found: {self.feature_names_path}")
            
            # Load feature names
            with open(self.feature_names_path, 'r', encoding='utf-8') as f:
                self.feature_names = json.load(f)
            
            # Validate feature names
            if not isinstance(self.feature_names, list) or len(self.feature_names) == 0:
                raise ValueError("Invalid feature names: must be non-empty list")
            
            logger.info("✓ Feature names loaded successfully")
            logger.info(f"  Features ({len(self.feature_names)}): {', '.join(self.feature_names)}")
            
            return self.feature_names
            
        except FileNotFoundError as e:
            logger.error(f"Feature names file not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load feature names: {str(e)}", exc_info=True)
            raise
    
    def load_metadata(self) -> Dict[str, Any]:
        """
        Load model metadata from JSON file (optional).
        
        Returns:
            Dictionary with model metadata
        """
        if not self.metadata_path:
            logger.warning("No metadata path configured")
            return {}
        
        try:
            logger.info(f"Loading model metadata from {self.metadata_path}")
            
            metadata_file = Path(self.metadata_path)
            if not metadata_file.exists():
                logger.warning(f"Metadata file not found: {self.metadata_path}")
                return {
                    "version": "unknown",
                    "model_type": "RandomForestClassifier",
                    "loaded_at": str(Path().resolve())
                }
            
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            logger.info("✓ Model metadata loaded successfully")
            logger.info(f"  Version: {self.metadata.get('version', 'unknown')}")
            logger.info(f"  Trained: {self.metadata.get('trained_date', 'unknown')}")
            logger.info(f"  Accuracy: {self.metadata.get('accuracy', 0.0):.4f}")
            
            return self.metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def initialize(self) -> None:
        """
        Initialize service by loading all model artifacts.
        
        Raises:
            Exception: If any loading step fails
        """
        if self.is_loaded:
            logger.info("Model already loaded, skipping initialization")
            return
        
        logger.info("="*80)
        logger.info("INITIALIZING ML MODEL INFERENCE SERVICE")
        logger.info("="*80)
        
        try:
            # Load all artifacts in order
            self.load_model()
            self.load_scaler()
            self.load_feature_names()
            self.load_metadata()
            
            # Validate compatibility
            self._validate_artifacts()
            
            self.is_loaded = True
            
            logger.info("="*80)
            logger.info("✓ MODEL INFERENCE SERVICE INITIALIZED SUCCESSFULLY")
            logger.info("="*80)
            logger.info(f"Model: {type(self.model).__name__}")
            logger.info(f"Features: {len(self.feature_names)}")
            logger.info(f"Version: {self.metadata.get('version', 'unknown')}")
            logger.info("Ready for predictions!")
            logger.info("="*80)
            
        except Exception as e:
            logger.error("="*80)
            logger.error("✗ MODEL INITIALIZATION FAILED")
            logger.error("="*80)
            logger.error(f"Error: {str(e)}")
            logger.error("="*80)
            raise
    
    def _validate_artifacts(self) -> None:
        """
        Validate that all loaded artifacts are compatible.
        
        Raises:
            ValueError: If artifacts are incompatible
        """
        # Check that all required artifacts are loaded
        if self.model is None:
            raise ValueError("Model not loaded")
        if self.scaler is None:
            raise ValueError("Scaler not loaded")
        if not self.feature_names:
            raise ValueError("Feature names not loaded")
        
        # Validate feature count compatibility
        expected_features = len(self.feature_names)
        scaler_features = getattr(self.scaler, 'n_features_in_', None)
        
        if scaler_features and scaler_features != expected_features:
            raise ValueError(
                f"Feature count mismatch: scaler expects {scaler_features}, "
                f"but feature names has {expected_features}"
            )
        
        logger.info("✓ Artifact validation passed")
    
    def predict_failure(self, sensor_data: Dict[str, float], equipment_id: str = "unknown") -> Dict[str, Any]:
        """
        Predict equipment failure probability and severity.
        
        Args:
            sensor_data: Dict with sensor readings:
                - temperature: Temperature in Celsius
                - vibration: Vibration in mm/s  
                - pressure: Pressure in bar
                - humidity: Humidity percentage (optional)
                - voltage: Voltage in volts (optional)
            equipment_id: Equipment identifier for logging
        
        Returns:
            Dict with comprehensive prediction results:
                - failure_probability: float (0-1)
                - prediction: int (0 or 1)
                - severity: str (CRITICAL/HIGH/MEDIUM/LOW)
                - days_until_failure: int
                - health_score: float (0-100)
                - confidence: str (high/medium/low)
                - recommended_action: str
        
        Raises:
            RuntimeError: If model is not loaded
            ValueError: If sensor data is invalid
            KeyError: If required sensor readings are missing
        """
        if not self.is_loaded:
            raise RuntimeError(
                "Model not initialized. Call initialize() first or check model loading errors."
            )
        
        logger.info(f"Making failure prediction for equipment: {equipment_id}")
        
        try:
            # Prepare input features
            features = self._prepare_features(sensor_data)
            
            # Apply scaling
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            binary_prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            failure_probability = float(probabilities[1])  # Probability of class 1 (failure)
            
            # Calculate derived metrics
            severity, days_until_failure = self._calculate_severity(failure_probability)
            health_score = self._calculate_health_score(failure_probability)
            confidence = self._calculate_confidence(failure_probability)
            recommended_action = self._get_recommended_action(severity)
            
            # Build comprehensive result
            result = {
                "failure_probability": round(failure_probability, 4),
                "prediction": int(binary_prediction),
                "severity": severity,
                "days_until_failure": days_until_failure,
                "health_score": round(health_score, 1),
                "confidence": confidence,
                "recommended_action": recommended_action,
                "model_version": self.metadata.get("version", "unknown")
            }
            
            # Log prediction summary
            logger.info(
                f"Prediction for {equipment_id}: "
                f"failure_prob={failure_probability:.3f}, "
                f"severity={severity}, "
                f"health_score={health_score:.1f}, "
                f"action={recommended_action}"
            )
            
            return result
            
        except KeyError as e:
            error_msg = f"Missing required sensor reading: {str(e)}"
            logger.error(f"Prediction failed for {equipment_id}: {error_msg}")
            raise KeyError(error_msg)
            
        except ValueError as e:
            error_msg = f"Invalid sensor data: {str(e)}"
            logger.error(f"Prediction failed for {equipment_id}: {error_msg}")
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"Model inference error: {str(e)}"
            logger.error(f"Prediction failed for {equipment_id}: {error_msg}", exc_info=True)
            raise Exception(error_msg)
    
    def _prepare_features(self, sensor_data: Dict[str, float]) -> np.ndarray:
        """
        Convert sensor data dict to numpy array in correct feature order.
        
        Args:
            sensor_data: Dictionary with sensor readings
        
        Returns:
            2D NumPy array ready for model input
            
        Raises:
            KeyError: If required features are missing
            ValueError: If feature values are invalid
        """
        try:
            features_list = []
            missing_features = []
            invalid_features = []
            
            for feature_name in self.feature_names:
                value = sensor_data.get(feature_name)
                
                # Handle missing features
                if value is None:
                    if feature_name in ['humidity', 'voltage']:  # Optional features
                        value = 0.0
                        logger.debug(f"Using default value 0.0 for optional feature: {feature_name}")
                    else:
                        missing_features.append(feature_name)
                        continue
                
                # Validate feature value
                if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                    invalid_features.append(f"{feature_name}={value}")
                    continue
                
                features_list.append(float(value))
            
            # Check for errors
            if missing_features:
                raise KeyError(f"Missing required features: {', '.join(missing_features)}")
            
            if invalid_features:
                raise ValueError(f"Invalid feature values: {', '.join(invalid_features)}")
            
            # Convert to numpy array (2D for sklearn)
            features = np.array([features_list], dtype=np.float32)
            
            # Validate shape
            expected_shape = (1, len(self.feature_names))
            if features.shape != expected_shape:
                raise ValueError(f"Feature shape mismatch: got {features.shape}, expected {expected_shape}")
            
            logger.debug(f"Features prepared: shape={features.shape}, values={features_list}")
            
            return features
            
        except (KeyError, ValueError) as e:
            raise
        except Exception as e:
            raise ValueError(f"Failed to prepare features: {str(e)}")
    
    def _calculate_severity(self, failure_prob: float) -> Tuple[str, int]:
        """
        Calculate severity level and days until failure from probability.
        
        Args:
            failure_prob: Failure probability (0.0 to 1.0)
        
        Returns:
            Tuple of (severity_level, days_until_failure)
        """
        if failure_prob > 0.8:
            return "CRITICAL", 7  # Immediate action required
        elif failure_prob > 0.6:
            return "HIGH", 15     # Schedule maintenance soon
        elif failure_prob > 0.4:
            return "MEDIUM", 30   # Plan maintenance
        else:
            return "LOW", 60      # Normal operation
    
    def _calculate_health_score(self, failure_prob: float) -> float:
        """
        Calculate normalized health score (0-100).
        
        Health score represents overall equipment condition:
        - 90-100: Excellent condition
        - 70-89: Good condition  
        - 50-69: Fair condition (monitoring recommended)
        - 30-49: Poor condition (maintenance needed)
        - 0-29: Critical condition (immediate action required)
        
        Args:
            failure_prob: Failure probability (0.0 to 1.0)
        
        Returns:
            Health score between 0.0 and 100.0
        """
        health_score = (1.0 - failure_prob) * 100.0
        return max(0.0, min(100.0, health_score))  # Clamp to [0, 100]
    
    def _calculate_confidence(self, failure_prob: float) -> str:
        """
        Calculate prediction confidence level.
        
        High confidence when probability is near 0 or 1 (clear decision).
        Low confidence when probability is near 0.5 (uncertain).
        
        Args:
            failure_prob: Failure probability (0.0 to 1.0)
        
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        # Distance from decision boundary (0.5)
        distance = abs(failure_prob - 0.5)
        
        if distance >= 0.3:    # Very clear decision (prob < 0.2 or > 0.8)
            return "high"
        elif distance >= 0.15: # Moderately clear decision
            return "medium"
        else:                  # Close to boundary (uncertain)
            return "low"
    
    def _get_recommended_action(self, severity: str) -> str:
        """
        Get recommended maintenance action based on severity level.
        
        Args:
            severity: Severity level (CRITICAL/HIGH/MEDIUM/LOW)
        
        Returns:
            Recommended action string
        """
        action_map = {
            "CRITICAL": "Schedule immediate maintenance - equipment likely to fail within 7 days",
            "HIGH": "Schedule maintenance within 2 weeks - equipment showing signs of degradation", 
            "MEDIUM": "Plan maintenance within next month - monitor equipment closely",
            "LOW": "Continue normal operation - routine maintenance as scheduled"
        }
        
        return action_map.get(severity, "Monitor equipment and reassess")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive model information and metadata.
        
        Returns:
            Dictionary with detailed model information
        
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not initialized")
        
        model_info = {
            "model_type": self.metadata.get("model_type", type(self.model).__name__),
            "version": self.metadata.get("version", "unknown"),
            "trained_date": self.metadata.get("trained_date", "unknown"),
            "features": self.feature_names.copy(),
            "feature_count": len(self.feature_names),
            "accuracy": self.metadata.get("accuracy", 0.0),
            "precision": self.metadata.get("precision", 0.0),
            "recall": self.metadata.get("recall", 0.0),
            "f1_score": self.metadata.get("f1_score", 0.0),
            "roc_auc": self.metadata.get("roc_auc", 0.0),
            "is_loaded": self.is_loaded,
            "model_params": {
                "n_estimators": getattr(self.model, 'n_estimators', None),
                "max_depth": getattr(self.model, 'max_depth', None),
                "min_samples_split": getattr(self.model, 'min_samples_split', None),
                "min_samples_leaf": getattr(self.model, 'min_samples_leaf', None),
                "class_weight": str(getattr(self.model, 'class_weight', None))
            }
        }
        
        return model_info
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the model service.
        
        Returns:
            Dictionary with health status information
        """
        return {
            "service_name": "ModelInferenceService",
            "is_initialized": self.is_loaded,
            "model_loaded": self.model is not None,
            "scaler_loaded": self.scaler is not None,
            "features_loaded": len(self.feature_names) > 0,
            "feature_count": len(self.feature_names),
            "model_version": self.metadata.get("version", "unknown"),
            "load_attempts": self._load_attempts,
            "status": "healthy" if self.is_loaded else "unhealthy"
        }


# Global singleton instance
_model_service: Optional[ModelInferenceService] = None


def get_model_service() -> ModelInferenceService:
    """
    Get the global ModelInferenceService instance (singleton).
    
    Returns:
        ModelInferenceService instance
    """
    global _model_service
    if _model_service is None:
        _model_service = ModelInferenceService()
    return _model_service


# Legacy compatibility - maintain the original MLModel class for backward compatibility
class MLModel:
    """
    Legacy wrapper for backward compatibility.
    Delegates to ModelInferenceService.
    """
    
    def __init__(self):
        self._service = get_model_service()
    
    def load_model(self) -> None:
        """Load model (legacy method)."""
        self._service.initialize()
    
    def predict(self, sensor_data: Dict[str, float]) -> Dict[str, Any]:
        """Make prediction (legacy method)."""
        result = self._service.predict_failure(sensor_data)
        # Convert to legacy format
        return {
            "prediction": result["prediction"],
            "failure_probability": result["failure_probability"],
            "severity": result["severity"],
            "days_until_failure": result["days_until_failure"],
            "confidence": result["confidence"]
        }
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded (legacy property)."""
        return self._service.is_loaded
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get model metadata (legacy property)."""
        return self._service.metadata
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model info (legacy method)."""
        return self._service.get_model_info()


# Global model instance for backward compatibility
ml_model = MLModel()


def get_ml_model() -> MLModel:
    """
    Get the global ML model instance (legacy function).
    
    Returns:
        MLModel instance (backward compatibility wrapper)
    """
    return ml_model
