"""
Database connection and ORM models for Alert & Maintenance Service.

Uses SQLAlchemy async for non-blocking database operations.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, Boolean
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


class AlertDB(Base):
    """
    Database model for alerts.
    
    Stores alerts generated based on prediction severity.
    """
    __tablename__ = "alerts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    prediction_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    
    # Alert details
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MaintenanceScheduleDB(Base):
    """
    Database model for maintenance schedules.
    
    Stores scheduled maintenance based on predictions.
    """
    __tablename__ = "maintenance_schedules"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    alert_id: Mapped[str] = mapped_column(String(36), nullable=True)
    
    # Schedule details
    scheduled_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="SCHEDULED")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[str] = mapped_column(String(100), nullable=True)
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
