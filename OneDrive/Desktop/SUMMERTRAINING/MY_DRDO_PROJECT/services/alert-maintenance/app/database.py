"""
Database connection and session management for Alert & Maintenance service.

Provides async database engine, session management, and helper functions
for database operations with connection pooling and proper error handling.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text

from .config import settings
from .schemas import Base

logger = logging.getLogger(__name__)

# Global engine instance
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.
    
    Creates a single engine instance with connection pooling for the
    entire application lifecycle.
    
    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    global _engine
    
    if _engine is None:
        logger.info("Creating async database engine...")
        logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1]}")  # Hide credentials
        
        # Create engine with connection pooling
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before using
            poolclass=QueuePool,  # Use connection pooling
            future=True,
            # Connection arguments for PostgreSQL
            connect_args={
                "server_settings": {"jit": "off"},  # Disable JIT for better performance
                "command_timeout": 60,
                "timeout": 10,
            }
        )
        
        logger.info(
            f"✓ Database engine created: "
            f"pool_size={settings.DB_POOL_SIZE}, "
            f"max_overflow={settings.DB_MAX_OVERFLOW}"
        )
    
    return _engine


def get_session_maker() -> async_sessionmaker:
    """
    Get or create the async session maker.
    
    Returns:
        async_sessionmaker: Session factory for creating database sessions
    """
    global _async_session_maker
    
    if _async_session_maker is None:
        engine = get_engine()
        
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )
        
        logger.info("✓ Async session maker created")
    
    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    Provides a database session for FastAPI endpoints with automatic
    cleanup and error handling.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @app.get("/items/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    session_maker = get_session_maker()
    
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    Creates all tables defined in SQLAlchemy models if they don't exist.
    Should be called on application startup.
    
    Raises:
        Exception: If database initialization fails
    """
    logger.info("Initializing database...")
    
    try:
        engine = get_engine()
        
        # Create all tables
        async with engine.begin() as conn:
            # Drop all tables (only in development)
            if settings.DEBUG:
                logger.warning("DEBUG mode: Dropping all tables...")
                await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✓ Database initialized successfully")
        logger.info(f"  Tables created: {', '.join(Base.metadata.tables.keys())}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise


async def check_db_connection() -> bool:
    """
    Check database connection health.
    
    Attempts to execute a simple query to verify database connectivity.
    Used for health check endpoints.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        engine = get_engine()
        
        async with engine.connect() as conn:
            # Execute simple query
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
            
        logger.debug("Database connection check: OK")
        return True
        
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


async def close_db_connection() -> None:
    """
    Close database connection and cleanup resources.
    
    Should be called on application shutdown to properly close
    all database connections and release resources.
    """
    global _engine, _async_session_maker
    
    if _engine is not None:
        logger.info("Closing database connections...")
        
        try:
            await _engine.dispose()
            logger.info("✓ Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")
        
        _engine = None
        _async_session_maker = None


async def get_db_stats() -> dict:
    """
    Get database connection pool statistics.
    
    Returns information about the current state of the connection pool,
    useful for monitoring and debugging.
    
    Returns:
        dict: Pool statistics including size, checked out connections, etc.
    """
    engine = get_engine()
    pool = engine.pool
    
    stats = {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }
    
    return stats


class DatabaseHealthCheck:
    """
    Database health check helper class.
    
    Provides methods for checking database health and connectivity
    with detailed diagnostics.
    """
    
    @staticmethod
    async def check_connection() -> dict:
        """
        Perform comprehensive database health check.
        
        Returns:
            dict: Health check results with status and details
        """
        result = {
            "status": "unhealthy",
            "connected": False,
            "tables_exist": False,
            "pool_stats": {},
            "error": None
        }
        
        try:
            # Check basic connection
            is_connected = await check_db_connection()
            result["connected"] = is_connected
            
            if not is_connected:
                result["error"] = "Cannot connect to database"
                return result
            
            # Check if tables exist
            engine = get_engine()
            async with engine.connect() as conn:
                # Check for alerts table
                query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'alerts'
                    )
                """)
                result_proxy = await conn.execute(query)
                tables_exist = (await result_proxy.fetchone())[0]
                result["tables_exist"] = tables_exist
            
            # Get pool statistics
            result["pool_stats"] = await get_db_stats()
            
            # Set overall status
            if is_connected and tables_exist:
                result["status"] = "healthy"
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        
        return result
    
    @staticmethod
    async def check_tables() -> dict:
        """
        Check if all required tables exist.
        
        Returns:
            dict: Table existence status for each table
        """
        required_tables = ["alerts", "maintenance_tasks", "maintenance_history"]
        table_status = {}
        
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                for table_name in required_tables:
                    query = text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table_name}'
                        )
                    """)
                    result = await conn.execute(query)
                    exists = (await result.fetchone())[0]
                    table_status[table_name] = exists
        
        except Exception as e:
            logger.error(f"Error checking tables: {str(e)}")
            for table_name in required_tables:
                table_status[table_name] = False
        
        return table_status


# Create health check instance
db_health = DatabaseHealthCheck()
