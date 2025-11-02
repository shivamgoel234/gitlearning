"""
Shared validation functions for DRDO Equipment Maintenance Prediction System.

Provides common validation logic for equipment IDs, sensor readings, and data integrity.
"""

import re
from typing import Optional
from .constants import EQUIPMENT_ID_PATTERN, SENSOR_CONSTRAINTS


def validate_equipment_id(equipment_id: str) -> bool:
    """
    Validate equipment ID against DRDO pattern: TYPE-LOCATION-NUMBER.
    
    Valid examples: RADAR-LOC-001, AIRCRAFT-BASE-042, NAVAL-PORT-003
    Invalid examples: radar001, RADAR_001, R-1
    
    Args:
        equipment_id: Equipment identifier string
        
    Returns:
        True if valid, False otherwise
        
    Example:
        >>> validate_equipment_id("RADAR-LOC-001")
        True
        >>> validate_equipment_id("radar001")
        False
    """
    return bool(re.match(EQUIPMENT_ID_PATTERN, equipment_id))


def validate_sensor_value(sensor_type: str, value: float) -> tuple[bool, Optional[str]]:
    """
    Validate sensor reading against defined constraints.
    
    Args:
        sensor_type: Type of sensor (temperature, vibration, pressure, etc.)
        value: Sensor reading value
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_sensor_value("temperature", 85.5)
        (True, None)
        >>> validate_sensor_value("temperature", 999.0)
        (False, "Value 999.0 outside valid range [-50.0, 200.0] for temperature")
    """
    if sensor_type not in SENSOR_CONSTRAINTS:
        return False, f"Unknown sensor type: {sensor_type}"
    
    constraints = SENSOR_CONSTRAINTS[sensor_type]
    min_val = constraints["min"]
    max_val = constraints["max"]
    
    if not (min_val <= value <= max_val):
        return False, (
            f"Value {value} outside valid range [{min_val}, {max_val}] "
            f"for {sensor_type}"
        )
    
    return True, None


def normalize_equipment_id(equipment_id: str) -> str:
    """
    Normalize equipment ID to uppercase format.
    
    Args:
        equipment_id: Equipment identifier string
        
    Returns:
        Normalized equipment ID in uppercase
        
    Example:
        >>> normalize_equipment_id("radar-loc-001")
        "RADAR-LOC-001"
    """
    return equipment_id.upper()
