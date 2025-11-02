"""
SQLAlchemy database schema models.

Defines the database table structure for sensor data storage.
"""

from sqlalchemy import Column, String, Float, DateTime, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime

Base = declarative_base()


class SensorDataDB(Base):
    """
    Database model for sensor readings.
    
    Stores all incoming sensor data with timestamps and equipment information.
    Indexed on equipment_id and timestamp for efficient querying.
    """
    
    __tablename__ = "sensor_data"
    
    # Primary key
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique reading identifier (UUID)"
    )
    
    # Equipment identifier
    equipment_id = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Equipment identifier (TYPE-LOCATION-NNN format)"
    )
    
    # Sensor readings
    temperature = Column(
        Float,
        nullable=False,
        comment="Temperature in Celsius"
    )
    
    vibration = Column(
        Float,
        nullable=False,
        comment="Vibration level in mm/s"
    )
    
    pressure = Column(
        Float,
        nullable=False,
        comment="Pressure in bar"
    )
    
    humidity = Column(
        Float,
        nullable=True,
        comment="Humidity percentage"
    )
    
    voltage = Column(
        Float,
        nullable=True,
        comment="Voltage in volts"
    )
    
    # Timestamps
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Sensor reading timestamp (UTC)"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp (UTC)"
    )
    
    # Composite indexes for efficient querying
    __table_args__ = (
        Index(
            'idx_equipment_timestamp',
            'equipment_id',
            'timestamp',
            postgresql_ops={'timestamp': 'DESC'}
        ),
        Index(
            'idx_timestamp_desc',
            'timestamp',
            postgresql_ops={'timestamp': 'DESC'}
        ),
    )
    
    def __repr__(self) -> str:
        """String representation of sensor data record."""
        return (
            f"<SensorData("
            f"id={self.id}, "
            f"equipment={self.equipment_id}, "
            f"temp={self.temperature}, "
            f"timestamp={self.timestamp}"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert database model to dictionary.
        
        Returns:
            Dictionary representation of the sensor reading
        """
        return {
            "reading_id": self.id,
            "equipment_id": self.equipment_id,
            "temperature": self.temperature,
            "vibration": self.vibration,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "voltage": self.voltage,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
