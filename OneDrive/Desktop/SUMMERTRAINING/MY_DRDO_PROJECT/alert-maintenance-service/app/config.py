"""
Configuration settings for Alert & Maintenance Service.

All configuration is loaded from environment variables following 12-factor app principles.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Service configuration loaded from environment variables."""
    
    # Service Identity
    SERVICE_NAME: str = "alert-maintenance"
    PORT: int = 8003
    DEBUG: bool = False
    
    # Database Configuration (REQUIRED)
    DATABASE_URL: str
    
    # Redis Configuration (REQUIRED)
    REDIS_URL: str
    
    # ML Prediction Service URL (REQUIRED)
    ML_PREDICTION_URL: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Alert Thresholds
    CRITICAL_ALERT_THRESHOLD: float = 0.8
    HIGH_ALERT_THRESHOLD: float = 0.6
    
    # Maintenance Scheduling
    CRITICAL_MAINTENANCE_DAYS: int = 7
    HIGH_MAINTENANCE_DAYS: int = 15
    MEDIUM_MAINTENANCE_DAYS: int = 30
    
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
