"""
Database connection and session management.

Implements async SQLAlchemy with connection pooling and health checks.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import settings
from .schemas import Base

logger = logging.getLogger(__name__)

# Global engine instance
engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_db_engine() -> None:
    """
    Initialize database engine with connection pooling.
    
    Called during application startup.
    """
    global engine, AsyncSessionLocal
    
    logger.info(f"Initializing database connection to {settings.DATABASE_URL.split('@')[-1]}")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=30,
            connect_args={
                "timeout": 10,
                "command_timeout": 10,
            }
        )
        
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info("Database engine initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {str(e)}", exc_info=True)
        raise


async def init_db_tables() -> None:
    """
    Create database tables if they don't exist.
    
    Called during application startup after engine initialization.
    """
    if engine is None:
        raise RuntimeError("Database engine not initialized")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created/verified successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
        raise


async def close_db_engine() -> None:
    """
    Close database engine and dispose of connections.
    
    Called during application shutdown.
    """
    global engine
    
    if engine is not None:
        logger.info("Closing database connections")
        await engine.dispose()
        logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session injection.
    
    Yields database session and ensures proper cleanup.
    Handles transaction rollback on exceptions.
    
    Yields:
        AsyncSession: Database session
        
    Usage:
        @app.post("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db_engine() first.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """
    Check database connectivity for health checks.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    if engine is None:
        logger.warning("Database engine not initialized")
        return False
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.
    
    Alternative to dependency injection for use in background tasks.
    
    Usage:
        async with get_db_context() as db:
            # Use db here
            pass
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database transaction error: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
