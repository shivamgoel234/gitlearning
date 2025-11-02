"""
Business logic for Sensor Data Ingestion Service.

Handles sensor data processing, validation, and storage with Redis pub/sub notification.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from .models import SensorReading, SensorReadingResponse
from .database import SensorDataDB
from .config import settings

logger = logging.getLogger(__name__)


class SensorIngestionService:
    """Service class for sensor data ingestion operations."""
    
    def __init__(self):
        """Initialize service with Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
    
    async def init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}", exc_info=True)
            raise
    
    async def close_redis(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def ingest_sensor_data(
        self,
        reading: SensorReading,
        db: AsyncSession
    ) -> SensorReadingResponse:
        """
        Ingest sensor data into database and publish event to Redis.
        
        Args:
            reading: Validated sensor reading data
            db: Database session
            
        Returns:
            SensorReadingResponse with reading ID and status
            
        Raises:
            Exception: If database or Redis operations fail
        """
        try:
            # Generate unique reading ID
            reading_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Create database record
            db_reading = SensorDataDB(
                id=reading_id,
                equipment_id=reading.equipment_id,
                timestamp=timestamp,
                temperature=reading.temperature,
                vibration=reading.vibration,
                pressure=reading.pressure,
                humidity=reading.humidity,
                voltage=reading.voltage,
                source=reading.source,
                notes=reading.notes,
            )
            
            # Save to database
            db.add(db_reading)
            await db.commit()
            await db.refresh(db_reading)
            
            logger.info(
                f"Sensor data ingested: reading_id={reading_id}, "
                f"equipment_id={reading.equipment_id}"
            )
            
            # Publish event to Redis for downstream services
            await self._publish_sensor_event(reading_id, reading, timestamp)
            
            return SensorReadingResponse(
                reading_id=reading_id,
                equipment_id=reading.equipment_id,
                timestamp=timestamp,
                status="received"
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to ingest sensor data: {e}", exc_info=True)
            raise
    
    async def _publish_sensor_event(
        self,
        reading_id: str,
        reading: SensorReading,
        timestamp: datetime
    ) -> None:
        """
        Publish sensor reading event to Redis pub/sub.
        
        Args:
            reading_id: Unique reading identifier
            reading: Sensor reading data
            timestamp: Reading timestamp
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized, skipping event publish")
            return
        
        try:
            event_data = {
                "event_type": "sensor_data_received",
                "reading_id": reading_id,
                "equipment_id": reading.equipment_id,
                "timestamp": timestamp.isoformat(),
                "data": {
                    "temperature": reading.temperature,
                    "vibration": reading.vibration,
                    "pressure": reading.pressure,
                    "humidity": reading.humidity,
                    "voltage": reading.voltage,
                }
            }
            
            await self.redis_client.publish(
                "sensor_data_channel",
                json.dumps(event_data)
            )
            
            logger.debug(f"Published sensor event for reading_id={reading_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish sensor event: {e}", exc_info=True)
            # Don't raise - event publishing is non-critical
    
    async def get_latest_readings(
        self,
        equipment_id: str,
        limit: int,
        db: AsyncSession
    ) -> list[SensorDataDB]:
        """
        Retrieve latest sensor readings for an equipment.
        
        Args:
            equipment_id: Equipment identifier
            limit: Maximum number of readings to retrieve
            db: Database session
            
        Returns:
            List of sensor readings ordered by timestamp (newest first)
        """
        try:
            stmt = select(SensorDataDB).where(
                SensorDataDB.equipment_id == equipment_id
            ).order_by(SensorDataDB.timestamp.desc()).limit(limit)
            
            result = await db.execute(stmt)
            readings = result.scalars().all()
            
            logger.debug(
                f"Retrieved {len(readings)} readings for equipment_id={equipment_id}"
            )
            
            return readings
            
        except Exception as e:
            logger.error(f"Failed to retrieve readings: {e}", exc_info=True)
            raise


# Global service instance
sensor_service = SensorIngestionService()
