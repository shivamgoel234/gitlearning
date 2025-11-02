"""
Tests for Sensor Data Ingestion Service.

Tests API endpoints, validation, and business logic.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.main import app
from app.models import SensorReading


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def valid_sensor_data():
    """Valid sensor reading data."""
    return {
        "equipment_id": "RADAR-LOC-001",
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0,
        "source": "iot-sensor-01",
        "notes": "Regular monitoring"
    }


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sensor-ingestion"
        assert "timestamp" in data


class TestSensorIngestion:
    """Test sensor data ingestion endpoints."""
    
    def test_ingest_sensor_data_valid(self, client, valid_sensor_data):
        """Test successful sensor data ingestion."""
        with patch("app.services.sensor_service.ingest_sensor_data") as mock_ingest:
            mock_ingest.return_value = AsyncMock(
                reading_id="test-id-123",
                equipment_id="RADAR-LOC-001",
                timestamp=datetime.utcnow(),
                status="received"
            )
            
            response = client.post("/api/v1/sensors/ingest", json=valid_sensor_data)
            
            assert response.status_code in [200, 201]
    
    def test_ingest_sensor_data_invalid_equipment_id(self, client, valid_sensor_data):
        """Test validation error for invalid equipment ID."""
        invalid_data = valid_sensor_data.copy()
        invalid_data["equipment_id"] = "invalid-id"
        
        response = client.post("/api/v1/sensors/ingest", json=invalid_data)
        assert response.status_code == 422
    
    def test_ingest_sensor_data_invalid_temperature(self, client, valid_sensor_data):
        """Test validation error for invalid temperature."""
        invalid_data = valid_sensor_data.copy()
        invalid_data["temperature"] = 999.0  # Outside valid range
        
        response = client.post("/api/v1/sensors/ingest", json=invalid_data)
        assert response.status_code == 422
    
    def test_ingest_sensor_data_invalid_vibration(self, client, valid_sensor_data):
        """Test validation error for invalid vibration."""
        invalid_data = valid_sensor_data.copy()
        invalid_data["vibration"] = -1.0  # Negative value
        
        response = client.post("/api/v1/sensors/ingest", json=invalid_data)
        assert response.status_code == 422
    
    def test_ingest_sensor_data_missing_required_field(self, client, valid_sensor_data):
        """Test validation error for missing required field."""
        invalid_data = valid_sensor_data.copy()
        del invalid_data["temperature"]
        
        response = client.post("/api/v1/sensors/ingest", json=invalid_data)
        assert response.status_code == 422


class TestSensorReadingModel:
    """Test Pydantic model validation."""
    
    def test_equipment_id_normalization(self):
        """Test equipment ID is normalized to uppercase."""
        data = {
            "equipment_id": "radar-loc-001",
            "temperature": 85.5,
            "vibration": 0.45,
            "pressure": 3.2
        }
        reading = SensorReading(**data)
        assert reading.equipment_id == "RADAR-LOC-001"
    
    def test_equipment_id_validation_pattern(self):
        """Test equipment ID pattern validation."""
        invalid_ids = ["radar001", "RADAR_001", "R-1", "RADAR-LOC-1"]
        
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError):
                SensorReading(
                    equipment_id=invalid_id,
                    temperature=85.5,
                    vibration=0.45,
                    pressure=3.2
                )
    
    def test_temperature_range_validation(self):
        """Test temperature range validation."""
        # Test minimum
        with pytest.raises(ValueError):
            SensorReading(
                equipment_id="RADAR-LOC-001",
                temperature=-100.0,
                vibration=0.45,
                pressure=3.2
            )
        
        # Test maximum
        with pytest.raises(ValueError):
            SensorReading(
                equipment_id="RADAR-LOC-001",
                temperature=300.0,
                vibration=0.45,
                pressure=3.2
            )
    
    def test_optional_fields(self):
        """Test optional fields."""
        reading = SensorReading(
            equipment_id="RADAR-LOC-001",
            temperature=85.5,
            vibration=0.45,
            pressure=3.2
        )
        assert reading.humidity is None
        assert reading.voltage is None
        assert reading.source is None
        assert reading.notes is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
