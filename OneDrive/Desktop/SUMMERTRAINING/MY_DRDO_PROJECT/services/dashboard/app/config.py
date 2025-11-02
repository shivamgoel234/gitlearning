"""
Configuration module for Dashboard service.

Loads configuration from environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    # Service Configuration
    SERVICE_NAME: str = "dashboard-service"
    SERVICE_VERSION: str = "1.0.0"
    PORT: int = 8004
    
    # Microservices URLs
    ALERT_SERVICE_URL: str = "http://localhost:8003"
    ML_SERVICE_URL: str = "http://localhost:8002"
    SENSOR_SERVICE_URL: str = "http://localhost:8001"
    
    # API Configuration
    API_TIMEOUT: int = 5  # seconds
    CACHE_TTL: int = 30  # seconds
    MAX_ALERTS_DISPLAY: int = 50
    
    # Dashboard Configuration
    REFRESH_INTERVAL: int = 30  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()
