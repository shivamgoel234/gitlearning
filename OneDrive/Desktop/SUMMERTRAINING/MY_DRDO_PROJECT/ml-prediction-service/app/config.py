"""
Configuration settings for ML Prediction Service.

All configuration is loaded from environment variables following 12-factor app principles.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Service configuration loaded from environment variables."""
    
    # Service Identity
    SERVICE_NAME: str = "ml-prediction"
    PORT: int = 8002
    DEBUG: bool = False
    
    # Database Configuration (REQUIRED)
    DATABASE_URL: str
    
    # Redis Configuration (REQUIRED)
    REDIS_URL: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # ML Model Configuration
    MODEL_PATH: str = "models/failure_predictor_v1.pkl"
    MODEL_METADATA_PATH: str = "models/model_metadata_v1.json"
    
    # Prediction Thresholds
    CRITICAL_THRESHOLD: float = 0.8
    HIGH_THRESHOLD: float = 0.6
    MEDIUM_THRESHOLD: float = 0.4
    LOW_THRESHOLD: float = 0.0
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]
    
    # Database Connection Pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
