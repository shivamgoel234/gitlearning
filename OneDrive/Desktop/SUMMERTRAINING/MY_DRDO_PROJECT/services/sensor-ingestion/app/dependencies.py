"""
Dependency injection functions for FastAPI.

Provides reusable dependencies for request handling.
"""

import redis.asyncio as redis_async
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: redis_async.Redis | None = None


async def init_redis() -> None:
    """
    Initialize Redis connection pool.
    
    Called during application startup.
    """
    global redis_client
    
    logger.info(f"Initializing Redis connection to {settings.REDIS_URL}")
    
    try:
        redis_client = redis_async.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        )
        
        # Test connection
        await redis_client.ping()
        
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {str(e)}", exc_info=True)
        raise


async def close_redis() -> None:
    """
    Close Redis connection.
    
    Called during application shutdown.
    """
    global redis_client
    
    if redis_client is not None:
        logger.info("Closing Redis connection")
        await redis_client.close()
        logger.info("Redis connection closed")


async def get_redis() -> redis_async.Redis:
    """
    Dependency for Redis client injection.
    
    Returns:
        Redis client instance
        
    Usage:
        @app.post("/endpoint")
        async def endpoint(redis: Redis = Depends(get_redis)):
            # Use redis here
            pass
    """
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    
    return redis_client


async def check_redis_connection() -> bool:
    """
    Check Redis connectivity for health checks.
    
    Returns:
        bool: True if Redis is accessible, False otherwise
    """
    if redis_client is None:
        logger.warning("Redis client not initialized")
        return False
    
    try:
        await redis_client.ping()
        return True
        
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False
