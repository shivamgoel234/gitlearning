"""
Configuration module for Sensor Ingestion Service.

Uses pydantic-settings for type-safe environment variable management
following 12-factor app principles.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All configuration MUST be provided via environment variables or .env file.
    NEVER hardcode sensitive values like database URLs or API keys.
    """
    
    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    SERVICE_NAME: str = "sensor-ingestion-service"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    DATABASE_URL: str  # REQUIRED - No default, must be set
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DB_ECHO: bool = False  # SQLAlchemy query logging
    
    # ============================================================================
    # REDIS CONFIGURATION
    # ============================================================================
    REDIS_URL: str  # REQUIRED - Format: redis://localhost:6379/0
    REDIS_QUEUE_NAME: str = "sensor_data_queue"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # ============================================================================
    # API CONFIGURATION
    # ============================================================================
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or text
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: str = "./logs/sensor-ingestion.log"
    
    # ============================================================================
    # SENSOR VALIDATION RULES
    # ============================================================================
    # Temperature (Celsius)
    MIN_TEMPERATURE: float = -50.0
    MAX_TEMPERATURE: float = 200.0
    
    # Vibration (mm/s)
    MIN_VIBRATION: float = 0.0
    MAX_VIBRATION: float = 2.0
    
    # Pressure (bar)
    MIN_PRESSURE: float = 0.0
    MAX_PRESSURE: float = 10.0
    
    # Humidity (%)
    MIN_HUMIDITY: float = 0.0
    MAX_HUMIDITY: float = 100.0
    
    # Voltage (V)
    MIN_VOLTAGE: float = 0.0
    MAX_VOLTAGE: float = 500.0
    
    # Equipment ID pattern (regex)
    EQUIPMENT_ID_PATTERN: str = r"^[A-Z]+-[A-Z0-9]+-\d{3}$"
    
    # ============================================================================
    # HEALTH CHECK CONFIGURATION
    # ============================================================================
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    HEALTH_CHECK_TIMEOUT: int = 10  # seconds
    
    # ============================================================================
    # METRICS CONFIGURATION
    # ============================================================================
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # ============================================================================
    # RETRY CONFIGURATION
    # ============================================================================
    REDIS_RETRY_ATTEMPTS: int = 3
    REDIS_RETRY_DELAY: float = 1.0  # seconds
    DB_RETRY_ATTEMPTS: int = 3
    DB_RETRY_DELAY: float = 0.5  # seconds
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency for injecting settings.
    
    Returns:
        Settings instance
    """
    return settings
