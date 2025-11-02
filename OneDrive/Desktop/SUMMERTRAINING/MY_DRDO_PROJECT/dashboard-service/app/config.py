"""
Configuration settings for Dashboard Service.

All configuration is loaded from environment variables following 12-factor app principles.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration loaded from environment variables."""
    
    # Service Identity
    SERVICE_NAME: str = "dashboard"
    PORT: int = 8004
    DEBUG: bool = False
    
    # Database Configuration (REQUIRED - read-only access)
    DATABASE_URL: str
    
    # Redis Configuration (REQUIRED)
    REDIS_URL: str
    
    # Microservice URLs (REQUIRED)
    SENSOR_INGESTION_URL: str
    ML_PREDICTION_URL: str
    ALERT_MAINTENANCE_URL: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]
    
    # Database Connection Pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    
    # Cache TTL (seconds)
    CACHE_TTL: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
