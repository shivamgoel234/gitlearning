"""
Shared constants for DRDO Equipment Maintenance Prediction System.

Contains sensor constraints, severity thresholds, and equipment validation rules.
"""

from typing import Dict, Any

# Sensor Value Constraints (DRDO-specific ranges)
SENSOR_CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    "temperature": {"min": -50.0, "max": 200.0, "unit": "°C"},
    "vibration": {"min": 0.0, "max": 2.0, "unit": "mm/s"},
    "pressure": {"min": 0.0, "max": 10.0, "unit": "bar"},
    "humidity": {"min": 0.0, "max": 100.0, "unit": "%"},
    "voltage": {"min": 0.0, "max": 500.0, "unit": "V"},
}

# Failure Severity Thresholds
SEVERITY_THRESHOLDS: Dict[str, float] = {
    "CRITICAL": 0.8,  # >80% failure probability
    "HIGH": 0.6,      # 60-80%
    "MEDIUM": 0.4,    # 40-60%
    "LOW": 0.0,       # <40%
}

# Health Score Ranges
HEALTH_SCORE_RANGES: Dict[str, Dict[str, Any]] = {
    "EXCELLENT": {"min": 90, "max": 100, "description": "Excellent condition"},
    "GOOD": {"min": 70, "max": 89, "description": "Good condition"},
    "FAIR": {"min": 50, "max": 69, "description": "Fair condition (monitoring recommended)"},
    "POOR": {"min": 30, "max": 49, "description": "Poor condition (maintenance needed)"},
    "CRITICAL": {"min": 0, "max": 29, "description": "Critical condition (immediate action required)"},
}

# Equipment ID Pattern
EQUIPMENT_ID_PATTERN: str = r'^[A-Z]+-[A-Z0-9]+-\d{3}$'

# API Version
API_VERSION: str = "v1"
API_PREFIX: str = f"/api/{API_VERSION}"

# Service Names
SERVICE_NAMES = {
    "SENSOR_INGESTION": "sensor-ingestion",
    "ML_PREDICTION": "ml-prediction",
    "ALERT_MAINTENANCE": "alert-maintenance",
    "DASHBOARD": "dashboard",
}
