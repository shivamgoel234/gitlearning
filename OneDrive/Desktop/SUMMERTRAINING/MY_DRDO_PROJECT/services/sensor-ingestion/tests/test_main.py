"""
Integration tests for the sensor ingestion service.

Tests all API endpoints, error handling, and validation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# Note: Import app after mocking dependencies
from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.lpush = AsyncMock()
    redis.ping = AsyncMock()
    return redis


@pytest.fixture
def valid_sensor_reading():
    """Valid sensor reading data."""
    return {
        "equipment_id": "RADAR-LOC-001",
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0
    }


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_health_check_healthy(client):
    """Test health check endpoint when all services are healthy."""
    with patch('app.database.check_db_connection', return_value=True), \
         patch('app.dependencies.check_redis_connection', return_value=True):
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "sensor-ingestion-service"
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["redis"] == "connected"


def test_health_check_unhealthy_database(client):
    """Test health check when database is down."""
    with patch('app.database.check_db_connection', return_value=False), \
         patch('app.dependencies.check_redis_connection', return_value=True):
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"


def test_readiness_check_ready(client):
    """Test readiness check when all services are ready."""
    with patch('app.database.check_db_connection', return_value=True), \
         patch('app.dependencies.check_redis_connection', return_value=True):
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["checks"]["database"] == "ready"
        assert data["checks"]["redis"] == "ready"


def test_readiness_check_not_ready(client):
    """Test readiness check when services are not ready."""
    with patch('app.database.check_db_connection', return_value=False), \
         patch('app.dependencies.check_redis_connection', return_value=False):
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is False


# ============================================================================
# SENSOR DATA INGESTION TESTS
# ============================================================================

def test_ingest_sensor_data_success(client, valid_sensor_reading, mock_db_session, mock_redis_client):
    """Test successful sensor data ingestion."""
    with patch('app.database.get_db', return_value=mock_db_session), \
         patch('app.dependencies.get_redis', return_value=mock_redis_client):
        
        response = client.post(
            "/api/v1/sensors/ingest",
            json=valid_sensor_reading
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "received"
        assert data["equipment_id"] == "RADAR-LOC-001"
        assert "reading_id" in data
        assert "timestamp" in data


def test_ingest_sensor_data_invalid_equipment_id(client, valid_sensor_reading):
    """Test ingestion with invalid equipment ID format."""
    invalid_reading = valid_sensor_reading.copy()
    invalid_reading["equipment_id"] = "invalid-format"
    
    response = client.post(
        "/api/v1/sensors/ingest",
        json=invalid_reading
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data


def test_ingest_sensor_data_temperature_out_of_range(client, valid_sensor_reading):
    """Test ingestion with temperature out of valid range."""
    invalid_reading = valid_sensor_reading.copy()
    invalid_reading["temperature"] = 999.0  # Above max
    
    response = client.post(
        "/api/v1/sensors/ingest",
        json=invalid_reading
    )
    
    assert response.status_code == 422


def test_ingest_sensor_data_vibration_out_of_range(client, valid_sensor_reading):
    """Test ingestion with vibration out of valid range."""
    invalid_reading = valid_sensor_reading.copy()
    invalid_reading["vibration"] = -1.0  # Below min
    
    response = client.post(
        "/api/v1/sensors/ingest",
        json=invalid_reading
    )
    
    assert response.status_code == 422


def test_ingest_sensor_data_missing_required_fields(client):
    """Test ingestion with missing required fields."""
    incomplete_reading = {
        "equipment_id": "RADAR-LOC-001",
        "temperature": 85.5
        # Missing vibration and pressure
    }
    
    response = client.post(
        "/api/v1/sensors/ingest",
        json=incomplete_reading
    )
    
    assert response.status_code == 422


def test_ingest_sensor_data_lowercase_equipment_id(client, valid_sensor_reading, mock_db_session, mock_redis_client):
    """Test that equipment ID is converted to uppercase."""
    reading = valid_sensor_reading.copy()
    reading["equipment_id"] = "radar-loc-001"
    
    with patch('app.database.get_db', return_value=mock_db_session), \
         patch('app.dependencies.get_redis', return_value=mock_redis_client):
        
        response = client.post(
            "/api/v1/sensors/ingest",
            json=reading
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["equipment_id"] == "RADAR-LOC-001"


# ============================================================================
# BATCH INGESTION TESTS
# ============================================================================

def test_ingest_batch_success(client, valid_sensor_reading, mock_db_session, mock_redis_client):
    """Test successful batch ingestion."""
    batch = {
        "readings": [
            valid_sensor_reading,
            {
                **valid_sensor_reading,
                "equipment_id": "RADAR-LOC-002"
            }
        ]
    }
    
    with patch('app.database.get_db', return_value=mock_db_session), \
         patch('app.dependencies.get_redis', return_value=mock_redis_client):
        
        response = client.post(
            "/api/v1/sensors/ingest/batch",
            json=batch
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 2
        assert data["successful"] == 2
        assert data["failed"] == 0
        assert len(data["reading_ids"]) == 2


def test_ingest_batch_partial_failure(client, valid_sensor_reading):
    """Test batch ingestion with some failures."""
    invalid_reading = valid_sensor_reading.copy()
    invalid_reading["temperature"] = 999.0
    
    batch = {
        "readings": [
            valid_sensor_reading,
            invalid_reading
        ]
    }
    
    response = client.post(
        "/api/v1/sensors/ingest/batch",
        json=batch
    )
    
    assert response.status_code == 201
    # Expect partial success


def test_ingest_batch_empty(client):
    """Test batch ingestion with empty list."""
    batch = {"readings": []}
    
    response = client.post(
        "/api/v1/sensors/ingest/batch",
        json=batch
    )
    
    assert response.status_code == 422


def test_ingest_batch_exceeds_limit(client, valid_sensor_reading):
    """Test batch ingestion exceeding max batch size."""
    batch = {
        "readings": [valid_sensor_reading] * 101  # Max is 100
    }
    
    response = client.post(
        "/api/v1/sensors/ingest/batch",
        json=batch
    )
    
    assert response.status_code == 422


# ============================================================================
# QUERY TESTS
# ============================================================================

def test_get_latest_readings(client, mock_db_session, mock_redis_client):
    """Test retrieving latest readings for equipment."""
    # Mock database query result
    mock_result = Mock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    with patch('app.database.get_db', return_value=mock_db_session), \
         patch('app.dependencies.get_redis', return_value=mock_redis_client):
        
        response = client.get("/api/v1/sensors/RADAR-LOC-001/latest")
        
        assert response.status_code == 200
        data = response.json()
        assert data["equipment_id"] == "RADAR-LOC-001"
        assert "readings" in data


def test_get_latest_readings_with_limit(client, mock_db_session, mock_redis_client):
    """Test retrieving readings with custom limit."""
    mock_result = Mock()
    mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    with patch('app.database.get_db', return_value=mock_db_session), \
         patch('app.dependencies.get_redis', return_value=mock_redis_client):
        
        response = client.get("/api/v1/sensors/RADAR-LOC-001/latest?limit=5")
        
        assert response.status_code == 200


def test_get_latest_readings_limit_exceeds_max(client):
    """Test that limit cannot exceed maximum."""
    response = client.get("/api/v1/sensors/RADAR-LOC-001/latest?limit=101")
    
    assert response.status_code == 400


# ============================================================================
# ROOT ENDPOINT TEST
# ============================================================================

def test_root_endpoint(client):
    """Test root endpoint returns service information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "sensor-ingestion-service"
    assert data["status"] == "running"
    assert "version" in data
    assert "docs" in data
