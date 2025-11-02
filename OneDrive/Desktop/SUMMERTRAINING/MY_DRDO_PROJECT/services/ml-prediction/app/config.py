"""
Configuration module for ML Prediction Service.

Uses pydantic-settings for type-safe environment variable management.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All configuration MUST be provided via environment variables or .env file.
    """
    
    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    SERVICE_NAME: str = "ml-prediction-service"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or text
    
    # ============================================================================
    # MODEL PATHS
    # ============================================================================
    MODEL_PATH: str = "./models/failure_predictor_v1.pkl"
    SCALER_PATH: str = "./models/scaler_v1.pkl"
    FEATURE_NAMES_PATH: str = "./models/feature_names_v1.json"
    METADATA_PATH: str = "./models/model_metadata_v1.json"
    
    # ============================================================================
    # API CONFIGURATION
    # ============================================================================
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # ============================================================================
    # PREDICTION CONFIGURATION
    # ============================================================================
    FAILURE_THRESHOLD: float = 0.5  # Probability threshold for failure prediction
    
    # Sensor value constraints (for validation)
    MIN_TEMPERATURE: float = -50.0
    MAX_TEMPERATURE: float = 200.0
    MIN_VIBRATION: float = 0.0
    MAX_VIBRATION: float = 2.0
    MIN_PRESSURE: float = 0.0
    MAX_PRESSURE: float = 10.0
    MIN_HUMIDITY: float = 0.0
    MAX_HUMIDITY: float = 100.0
    MIN_VOLTAGE: float = 0.0
    MAX_VOLTAGE: float = 500.0
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    def validate_model_paths(self) -> bool:
        """
        Validate that all model files exist.
        
        Returns:
            True if all required model files exist
        """
        required_files = [
            self.MODEL_PATH,
            self.SCALER_PATH,
            self.FEATURE_NAMES_PATH,
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            raise FileNotFoundError(
                f"Required model files not found: {', '.join(missing_files)}"
            )
        
        return True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency for injecting settings.
    
    Returns:
        Settings instance
    """
    return settings
