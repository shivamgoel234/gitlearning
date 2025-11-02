"""
Configuration settings for Sensor Data Ingestion Service.

All configuration is loaded from environment variables following 12-factor app principles.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Service configuration loaded from environment variables."""
    
    # Service Identity
    SERVICE_NAME: str = "sensor-ingestion"
    PORT: int = 8001
    DEBUG: bool = False
    
    # Database Configuration (REQUIRED)
    DATABASE_URL: str
    
    # Redis Configuration (REQUIRED)
    REDIS_URL: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Sensor Validation Constraints
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
