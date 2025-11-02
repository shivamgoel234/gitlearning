"""
Configuration module for Alert & Maintenance service.

Loads configuration from environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables.
    """
    
    # Service Configuration
    SERVICE_NAME: str = "alert-maintenance-service"
    SERVICE_VERSION: str = "1.0.0"
    PORT: int = 8003
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://drdo:drdo123@localhost:5432/equipment_maintenance"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    
    # External Service URLs
    ML_PREDICTION_SERVICE_URL: str = "http://localhost:8002"
    SENSOR_INGESTION_SERVICE_URL: str = "http://localhost:8001"
    
    # Email Configuration
    EMAIL_ENABLED: bool = True
    EMAIL_FROM: str = "alerts@drdo.gov.in"
    EMAIL_TO: str = "maintenance@drdo.gov.in"
    EMAIL_CC: Optional[str] = "ops@drdo.gov.in"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Alert Configuration
    ALERT_CRITICAL_THRESHOLD: float = 0.8
    ALERT_HIGH_THRESHOLD: float = 0.6
    ALERT_MEDIUM_THRESHOLD: float = 0.4
    AUTO_CREATE_TASKS: bool = True
    
    # Maintenance Task Configuration
    DEFAULT_TASK_DURATION: int = 4
    CRITICAL_PRIORITY_DAYS: int = 7
    HIGH_PRIORITY_DAYS: int = 15
    MEDIUM_PRIORITY_DAYS: int = 30
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8004"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_email_recipients(self) -> List[str]:
        """
        Get list of email recipients for alerts.
        
        Returns:
            List of email addresses
        """
        recipients = [self.EMAIL_TO]
        if self.EMAIL_CC:
            recipients.append(self.EMAIL_CC)
        return recipients
    
    def get_cors_origins_list(self) -> List[str]:
        """
        Get CORS origins as a list.
        
        Handles both string and list formats from environment variables.
        
        Returns:
            List of allowed origins
        """
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    def validate_database_url(self) -> None:
        """
        Validate database URL format.
        
        Raises:
            ValueError: If database URL is invalid
        """
        if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use asyncpg driver. "
                "Format: postgresql+asyncpg://user:password@host:port/database"
            )
    
    def get_severity_from_probability(self, failure_probability: float) -> str:
        """
        Determine alert severity based on failure probability.
        
        Args:
            failure_probability: Probability of failure (0.0 to 1.0)
        
        Returns:
            Severity level: CRITICAL, HIGH, MEDIUM, or LOW
        """
        if failure_probability >= self.ALERT_CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif failure_probability >= self.ALERT_HIGH_THRESHOLD:
            return "HIGH"
        elif failure_probability >= self.ALERT_MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_priority_from_severity(self, severity: str) -> str:
        """
        Map alert severity to maintenance task priority.
        
        Args:
            severity: Alert severity level
        
        Returns:
            Task priority: CRITICAL, HIGH, MEDIUM, or LOW
        """
        return severity  # Direct mapping for now
    
    def get_scheduled_days_from_priority(self, priority: str) -> int:
        """
        Get number of days until scheduled maintenance based on priority.
        
        Args:
            priority: Task priority level
        
        Returns:
            Number of days
        """
        priority_days_map = {
            "CRITICAL": self.CRITICAL_PRIORITY_DAYS,
            "HIGH": self.HIGH_PRIORITY_DAYS,
            "MEDIUM": self.MEDIUM_PRIORITY_DAYS,
            "LOW": self.MEDIUM_PRIORITY_DAYS * 2  # 60 days for LOW
        }
        return priority_days_map.get(priority, self.MEDIUM_PRIORITY_DAYS)


# Create global settings instance
settings = Settings()

# Validate settings on startup
try:
    settings.validate_database_url()
except ValueError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Database URL validation warning: {str(e)}")
