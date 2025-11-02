"""
Database connection and ORM models for ML Prediction Service.

Uses SQLAlchemy async for non-blocking database operations.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text
from datetime import datetime
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DEBUG,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class PredictionDB(Base):
    """
    Database model for ML predictions.
    
    Stores prediction results with failure probabilities and severity levels.
    """
    __tablename__ = "predictions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    
    # Prediction results
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    health_score: Mapped[float] = mapped_column(Float, nullable=False)
    days_until_failure: Mapped[int] = mapped_column(nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Input features
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    vibration: Mapped[float] = mapped_column(Float, nullable=False)
    pressure: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=True)
    voltage: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Metadata
    model_version: Mapped[str] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for database sessions.
    
    Yields:
        AsyncSession: Database session that automatically closes after use
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in Base metadata if they don't exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def close_db() -> None:
    """
    Close database engine and dispose of connections.
    
    Should be called during application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")
