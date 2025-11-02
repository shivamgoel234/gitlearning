"""
Business logic service layer.

Implements core sensor data ingestion logic with validation and queueing.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis_async
import json
import logging
from datetime import datetime
from typing import Optional
import uuid
import asyncio

from .models import SensorReading, SensorReadingResponse, SensorReadingBatchResponse
from .schemas import SensorDataDB
from .config import settings
from .exceptions import ValidationError, DatabaseError, RedisError, SensorAnomalyError

logger = logging.getLogger(__name__)


class SensorIngestionService:
    """
    Service for ingesting sensor data.
    
    Handles validation, database storage, and Redis queue publishing.
    """
    
    def __init__(self, db: AsyncSession, redis: redis_async.Redis):
        """
        Initialize service with dependencies.
        
        Args:
            db: Database session
            redis: Redis client
        """
        self.db = db
        self.redis = redis
    
    async def ingest_sensor_data(
        self,
        reading: SensorReading,
        request_id: Optional[str] = None
    ) -> SensorReadingResponse:
        """
        Ingest single sensor reading.
        
        Validates data, stores in database, and publishes to Redis queue
        for ML prediction service to consume.
        
        Args:
            reading: Sensor reading to ingest
            request_id: Optional request ID for tracing
            
        Returns:
            SensorReadingResponse with reading ID and status
            
        Raises:
            ValidationError: If sensor data fails validation
            DatabaseError: If database operation fails
            RedisError: If Redis operation fails
        """
        reading_id = str(uuid.uuid4())
        
        log_extra = {
            "equipment_id": reading.equipment_id,
            "reading_id": reading_id,
            "request_id": request_id
        }
        
        try:
            # Additional business validation
            self._validate_sensor_values(reading)
            
            # Store in database
            db_reading = await self._store_reading(reading_id, reading)
            
            logger.info(
                f"Sensor data stored: {reading_id} for {reading.equipment_id}",
                extra=log_extra
            )
            
            # Publish to Redis queue for ML service (non-blocking)
            try:
                await self._publish_to_queue(reading_id, reading)
            except Exception as e:
                # Log but don't fail - data is already persisted
                logger.warning(
                    f"Failed to publish to Redis queue: {str(e)}",
                    extra=log_extra
                )
            
            # Return success response
            return SensorReadingResponse(
                reading_id=reading_id,
                equipment_id=reading.equipment_id,
                timestamp=reading.timestamp,
                status="received",
                message="Sensor data ingested successfully"
            )
            
        except SensorAnomalyError as e:
            logger.warning(
                f"Sensor anomaly detected: {str(e)}",
                extra=log_extra
            )
            raise ValidationError(str(e))
            
        except Exception as e:
            logger.error(
                f"Error ingesting sensor data: {str(e)}",
                extra=log_extra,
                exc_info=True
            )
            await self.db.rollback()
            raise DatabaseError(f"Failed to ingest sensor data: {str(e)}")
    
    async def ingest_batch(
        self,
        readings: list[SensorReading],
        request_id: Optional[str] = None
    ) -> SensorReadingBatchResponse:
        """
        Ingest batch of sensor readings.
        
        Processes multiple readings, continuing on individual failures.
        
        Args:
            readings: List of sensor readings to ingest
            request_id: Optional request ID for tracing
            
        Returns:
            SensorReadingBatchResponse with success/failure counts
        """
        total = len(readings)
        successful_ids = []
        errors = []
        
        logger.info(
            f"Processing batch of {total} readings",
            extra={"request_id": request_id}
        )
        
        for idx, reading in enumerate(readings):
            try:
                response = await self.ingest_sensor_data(reading, request_id)
                successful_ids.append(response.reading_id)
                
            except Exception as e:
                errors.append({
                    "index": idx,
                    "equipment_id": reading.equipment_id,
                    "error": str(e)
                })
                logger.warning(
                    f"Failed to ingest reading {idx}: {str(e)}",
                    extra={"request_id": request_id}
                )
        
        successful = len(successful_ids)
        failed = total - successful
        
        logger.info(
            f"Batch processing complete: {successful}/{total} successful",
            extra={"request_id": request_id}
        )
        
        return SensorReadingBatchResponse(
            total=total,
            successful=successful,
            failed=failed,
            reading_ids=successful_ids,
            errors=errors
        )
    
    async def get_latest_readings(
        self,
        equipment_id: str,
        limit: int = 10
    ) -> list[dict]:
        """
        Retrieve latest sensor readings for equipment.
        
        Args:
            equipment_id: Equipment identifier
            limit: Maximum number of readings to return
            
        Returns:
            List of sensor readings as dictionaries
        """
        try:
            stmt = select(SensorDataDB).where(
                SensorDataDB.equipment_id == equipment_id
            ).order_by(
                SensorDataDB.timestamp.desc()
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            readings = result.scalars().all()
            
            return [reading.to_dict() for reading in readings]
            
        except Exception as e:
            logger.error(
                f"Error retrieving readings for {equipment_id}: {str(e)}",
                exc_info=True
            )
            raise DatabaseError(f"Failed to retrieve readings: {str(e)}")
    
    def _validate_sensor_values(self, reading: SensorReading) -> None:
        """
        Additional business validation beyond Pydantic.
        
        Checks for anomalous sensor combinations that may indicate failures.
        
        Args:
            reading: Sensor reading to validate
            
        Raises:
            SensorAnomalyError: If validation fails
        """
        # Check for sensor failure (all zeros)
        if (reading.temperature == 0 and 
            reading.vibration == 0 and 
            reading.pressure == 0):
            raise SensorAnomalyError(
                "All sensor readings are zero - possible sensor failure",
                details={
                    "equipment_id": reading.equipment_id,
                    "timestamp": reading.timestamp.isoformat()
                }
            )
        
        # Check for dangerous combinations
        if reading.temperature > 150 and reading.vibration > 1.5:
            logger.warning(
                f"High temperature ({reading.temperature}°C) AND high vibration "
                f"({reading.vibration} mm/s) detected for {reading.equipment_id}"
            )
        
        # Check for extremely low pressure with high temperature
        if reading.temperature > 100 and reading.pressure < 0.5:
            logger.warning(
                f"High temperature ({reading.temperature}°C) with low pressure "
                f"({reading.pressure} bar) for {reading.equipment_id}"
            )
    
    async def _store_reading(
        self,
        reading_id: str,
        reading: SensorReading
    ) -> SensorDataDB:
        """
        Store sensor reading in database.
        
        Args:
            reading_id: Unique reading identifier
            reading: Sensor reading to store
            
        Returns:
            Database model instance
            
        Raises:
            DatabaseError: If storage fails
        """
        try:
            db_reading = SensorDataDB(
                id=reading_id,
                equipment_id=reading.equipment_id,
                temperature=reading.temperature,
                vibration=reading.vibration,
                pressure=reading.pressure,
                humidity=reading.humidity,
                voltage=reading.voltage,
                timestamp=reading.timestamp
            )
            
            self.db.add(db_reading)
            await self.db.commit()
            await self.db.refresh(db_reading)
            
            return db_reading
            
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to store reading: {str(e)}")
    
    async def _publish_to_queue(
        self,
        reading_id: str,
        reading: SensorReading
    ) -> None:
        """
        Publish sensor data to Redis queue for ML service.
        
        Uses Redis LPUSH to add to queue. ML prediction service
        uses BRPOP to consume messages.
        
        Args:
            reading_id: Unique reading identifier
            reading: Sensor reading to publish
            
        Raises:
            RedisError: If publish fails
        """
        try:
            message = {
                "reading_id": reading_id,
                "equipment_id": reading.equipment_id,
                "temperature": reading.temperature,
                "vibration": reading.vibration,
                "pressure": reading.pressure,
                "humidity": reading.humidity,
                "voltage": reading.voltage,
                "timestamp": reading.timestamp.isoformat()
            }
            
            # Publish to Redis queue
            await self.redis.lpush(
                settings.REDIS_QUEUE_NAME,
                json.dumps(message)
            )
            
            logger.debug(
                f"Published reading {reading_id} to Redis queue",
                extra={
                    "reading_id": reading_id,
                    "equipment_id": reading.equipment_id
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to publish to Redis: {str(e)}",
                extra={
                    "reading_id": reading_id,
                    "equipment_id": reading.equipment_id
                }
            )
            raise RedisError(f"Failed to publish to queue: {str(e)}")
