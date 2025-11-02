"""
Celery application configuration for Alert & Maintenance service.

Minimal setup for background task processing with Redis as broker.
"""

from celery import Celery
import os
import logging

logger = logging.getLogger(__name__)

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery application
celery_app = Celery(
    "alert_maintenance_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"]  # Auto-discover tasks
)

# Minimal configuration for demo
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    task_time_limit=30,  # 30 seconds max per task
    task_soft_time_limit=25,  # Soft limit at 25 seconds
    
    # Results
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Disable rate limiting for demo
    task_default_rate_limit=None,
)

logger.info(f"Celery app configured with broker: {CELERY_BROKER_URL}")
