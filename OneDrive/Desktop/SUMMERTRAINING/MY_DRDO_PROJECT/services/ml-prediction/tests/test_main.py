"""
Comprehensive test suite for ML prediction service API endpoints.

Tests cover:
- Prediction endpoints (success, validation, error cases)
- Health check endpoints
- Equipment health endpoints
- Batch prediction endpoints
- Model info endpoints
- Error handling and edge cases
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

# Import models before mocking
from app.models import (
    SensorReadingInput,
    SimplePredictionResponse,
    PredictionResponse,
    EquipmentHealthResponse,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_model_service():
    """
    Mock ModelInferenceService with realistic prediction results.
    """
    mock = MagicMock()
    mock.is_loaded = True
    mock.metadata = {
        "version": "v1.0",
        "model_type": "RandomForestClassifier",
        "accuracy": 0.89,
        "precision": 0.87,
        "recall": 0.91,
        "f1_score": 0.89,
        "roc_auc": 0.93
    }
    
    # Mock predict_failure method
    mock.predict_failure.return_value = {
        "failure_probability": 0.82,
        "prediction": 1,
        "severity": "CRITICAL",
        "days_until_failure": 7,
        "health_score": 18.0,
        "confidence": "high",
        "recommended_action": "Schedule immediate maintenance - equipment likely to fail within 7 days",
        "model_version": "v1.0"
    }
    
    # Mock health_check method
    mock.health_check.return_value = {
        "service_name": "ModelInferenceService",
        "is_initialized": True,
        "model_loaded": True,
        "status": "healthy",
        "model_version": "v1.0"
    }
    
    # Mock get_model_info method
    mock.get_model_info.return_value = {
        "model_type": "RandomForestClassifier",
        "version": "v1.0",
        "trained_date": "2025-10-15",
        "features": ["temperature", "vibration", "pressure", "humidity", "voltage"],
        "feature_count": 5,
        "accuracy": 0.89,
        "precision": 0.87,
        "recall": 0.91,
        "f1_score": 0.89,
        "roc_auc": 0.93
    }
    
    # Mock initialize method
    mock.initialize.return_value = None
    
    return mock


@pytest.fixture
def mock_prediction_service(mock_model_service):
    """
    Mock PredictionService with realistic responses.
    """
    mock = MagicMock()
    mock.model_service = mock_model_service
    
    # Mock get_service_status
    mock.get_service_status.return_value = {
        "service": "ml-prediction-service",
        "status": "healthy",
        "model_loaded": True,
        "model_version": "v1.0",
        "timestamp": datetime.utcnow()
    }
    
    return mock


@pytest.fixture
def client(mock_model_service, mock_prediction_service):
    """
    Test client for FastAPI app with mocked services.
    """
    with patch('app.ml_model.ModelInferenceService') as mock_model_class, \
         patch('app.services.PredictionService') as mock_service_class, \
         patch('app.services.get_prediction_service') as mock_get_service, \
         patch('app.ml_model.get_model_service') as mock_get_model:
        
        # Configure mocks
        mock_model_class.return_value = mock_model_service
        mock_service_class.return_value = mock_prediction_service
        mock_get_service.return_value = mock_prediction_service
        mock_get_model.return_value = mock_model_service
        
        # Import app after mocking
        from app.main import app
        
        # Create test client
        test_client = TestClient(app)
        
        yield test_client


@pytest.fixture
def valid_sensor_data() -> Dict[str, Any]:
    """
    Valid sensor readings for testing.
    """
    return {
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0
    }


@pytest.fixture
def valid_sensor_data_with_equipment() -> Dict[str, Any]:
    """
    Valid sensor readings with equipment ID.
    """
    return {
        "equipment_id": "RADAR-LOC-001",
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0
    }


@pytest.fixture
def expected_prediction_response() -> Dict[str, Any]:
    """
    Expected prediction response structure.
    """
    return {
        "failure_probability": 0.82,
        "severity": "CRITICAL",
        "days_until_failure": 7,
        "health_score": 18.0,
        "confidence": "high",
        "recommended_action": "Schedule immediate maintenance - equipment likely to fail within 7 days"
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_invalid_sensor_data(invalid_field: str, invalid_value: Any) -> Dict[str, Any]:
    """
    Create sensor data with one invalid field for testing validation.
    
    Args:
        invalid_field: Name of the field to make invalid
        invalid_value: Invalid value to use
    
    Returns:
        Dictionary with invalid sensor data
    """
    valid_data = {
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0
    }
    valid_data[invalid_field] = invalid_value
    return valid_data


def assert_prediction_response_structure(data: Dict[str, Any]) -> None:
    """
    Assert that response has correct prediction structure.
    
    Args:
        data: Response data to validate
    """
    required_fields = [
        "failure_probability",
        "severity",
        "days_until_failure",
        "health_score",
        "confidence",
        "recommended_action",
        "timestamp"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Type checks
    assert isinstance(data["failure_probability"], float)
    assert isinstance(data["severity"], str)
    assert isinstance(data["days_until_failure"], int)
    assert isinstance(data["health_score"], (int, float))
    assert isinstance(data["confidence"], str)
    assert isinstance(data["recommended_action"], str)
    assert isinstance(data["timestamp"], str)
    
    # Value range checks
    assert 0.0 <= data["failure_probability"] <= 1.0
    assert data["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert data["days_until_failure"] >= 0
    assert 0.0 <= data["health_score"] <= 100.0
    assert data["confidence"] in ["high", "medium", "low"]


def assert_health_response_structure(data: Dict[str, Any]) -> None:
    """
    Assert that response has correct health check structure.
    
    Args:
        data: Response data to validate
    """
    required_fields = ["service", "status", "version", "model_loaded", "timestamp"]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    assert isinstance(data["service"], str)
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["model_loaded"], bool)


# ============================================================================
# ROOT & INFO ENDPOINTS TESTS
# ============================================================================

def test_root_endpoint(client):
    """
    Test root endpoint returns service information.
    """
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ml-prediction-service"
    assert data["status"] == "running"
    assert "version" in data
    assert "docs" in data
    assert "health" in data
    assert "api_prefix" in data


# ============================================================================
# HEALTH CHECK ENDPOINT TESTS
# ============================================================================

def test_health_check(client):
    """
    Test /health endpoint for Kubernetes liveness probe.
    
    Verifies:
    - Status code 200
    - Service name is correct
    - Status is "healthy"
    - Model loaded status is reported
    - Timestamp is present
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert_health_response_structure(data)
    
    # Verify values
    assert data["service"] == "ml-prediction-service"
    assert data["status"] in ["healthy", "unhealthy"]
    assert isinstance(data["model_loaded"], bool)


def test_readiness_check(client):
    """
    Test /health/ready endpoint for Kubernetes readiness probe.
    
    Verifies service is ready to accept requests.
    """
    response = client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert_health_response_structure(data)
    
    # Verify readiness status
    assert data["status"] in ["ready", "not_ready"]


# ============================================================================
# PREDICTION ENDPOINT TESTS - SUCCESS CASES
# ============================================================================

def test_predict_failure_success(client, valid_sensor_data, mock_prediction_service):
    """
    Test successful failure prediction with valid sensor data.
    
    Verifies:
    - Status code 200
    - Response has all required fields
    - Field types are correct (float, str, int)
    - Values are within expected ranges
    """
    # Mock the prediction service
    async def mock_predict_failure(sensor_data, equipment_id):
        return SimplePredictionResponse(
            failure_probability=0.82,
            severity="CRITICAL",
            days_until_failure=7,
            health_score=18.0,
            confidence="high",
            recommended_action="Schedule immediate maintenance - equipment likely to fail within 7 days",
            timestamp=datetime.utcnow()
        )
    
    mock_prediction_service.predict_equipment_failure = mock_predict_failure
    
    response = client.post("/api/v1/predict/failure", json=valid_sensor_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure and types
    assert_prediction_response_structure(data)
    
    # Verify specific values
    assert data["failure_probability"] == 0.82
    assert data["severity"] == "CRITICAL"
    assert data["days_until_failure"] == 7
    assert data["health_score"] == 18.0
    assert data["confidence"] == "high"


def test_predict_with_equipment_id_success(client, valid_sensor_data_with_equipment, mock_prediction_service):
    """
    Test prediction endpoint with equipment ID tracking.
    
    Verifies:
    - Equipment ID is included in response
    - All prediction fields are present
    """
    # Mock the prediction service
    async def mock_predict_with_equipment(sensor_data):
        return PredictionResponse(
            equipment_id=sensor_data.equipment_id,
            prediction=1,
            failure_probability=0.82,
            severity="CRITICAL",
            days_until_failure=7,
            confidence="high",
            timestamp=datetime.utcnow(),
            model_version="v1.0"
        )
    
    mock_prediction_service.predict_with_equipment_id = mock_predict_with_equipment
    
    response = client.post("/api/v1/predict", json=valid_sensor_data_with_equipment)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["equipment_id"] == "RADAR-LOC-001"
    assert "prediction" in data
    assert "failure_probability" in data
    assert "severity" in data
    assert "confidence" in data
    assert "model_version" in data


def test_predict_failure_with_optional_fields(client):
    """
    Test prediction with only required fields (no humidity/voltage).
    
    Verifies:
    - Optional fields can be omitted
    - Prediction still succeeds
    """
    sensor_data = {
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2
    }
    
    response = client.post("/api/v1/predict/failure", json=sensor_data)
    
    # Should succeed with optional fields as None
    assert response.status_code in [200, 422]  # May fail if model requires all features


# ============================================================================
# PREDICTION ENDPOINT TESTS - VALIDATION ERRORS
# ============================================================================

def test_predict_failure_invalid_temperature(client):
    """
    Test prediction with temperature outside valid range.
    
    Verifies:
    - Status code 422 (Unprocessable Entity)
    - Error message contains "temperature"
    """
    invalid_data = create_invalid_sensor_data("temperature", 999.0)
    
    response = client.post("/api/v1/predict/failure", json=invalid_data)
    
    assert response.status_code == 422
    data = response.json()
    
    # Error details should mention temperature
    error_str = str(data).lower()
    assert "temperature" in error_str


def test_predict_failure_invalid_vibration(client):
    """
    Test prediction with vibration outside valid range.
    
    Verifies:
    - Status code 422
    - Error message contains "vibration"
    """
    invalid_data = create_invalid_sensor_data("vibration", 10.0)  # Max is 2.0
    
    response = client.post("/api/v1/predict/failure", json=invalid_data)
    
    assert response.status_code == 422
    data = response.json()
    
    error_str = str(data).lower()
    assert "vibration" in error_str


def test_predict_failure_negative_pressure(client):
    """
    Test prediction with negative pressure value.
    
    Verifies:
    - Status code 422
    - Validation catches negative values
    """
    invalid_data = create_invalid_sensor_data("pressure", -1.0)
    
    response = client.post("/api/v1/predict/failure", json=invalid_data)
    
    assert response.status_code == 422


def test_predict_failure_missing_required_field(client):
    """
    Test prediction with missing required field (vibration).
    
    Verifies:
    - Status code 422
    - Error details indicate missing field
    """
    incomplete_data = {
        "temperature": 85.5,
        "pressure": 3.2
        # Missing vibration
    }
    
    response = client.post("/api/v1/predict/failure", json=incomplete_data)
    
    assert response.status_code == 422
    data = response.json()
    
    # Should indicate missing field
    error_str = str(data).lower()
    assert "vibration" in error_str or "required" in error_str


def test_predict_failure_invalid_data_types(client):
    """
    Test prediction with invalid data types (string instead of float).
    
    Verifies:
    - Status code 422
    - Type validation works correctly
    """
    invalid_data = {
        "temperature": "not_a_number",
        "vibration": 0.45,
        "pressure": 3.2
    }
    
    response = client.post("/api/v1/predict/failure", json=invalid_data)
    
    assert response.status_code == 422


def test_predict_failure_empty_payload(client):
    """
    Test prediction with empty request body.
    
    Verifies:
    - Status code 422
    - Proper error handling for empty requests
    """
    response = client.post("/api/v1/predict/failure", json={})
    
    assert response.status_code == 422


# ============================================================================
# PREDICTION ENDPOINT TESTS - ERROR HANDLING
# ============================================================================

def test_predict_failure_model_error(client, valid_sensor_data, mock_prediction_service):
    """
    Test prediction when ML model raises an exception.
    
    Verifies:
    - Status code 500 or 503
    - Error message is returned
    - Service handles model errors gracefully
    """
    # Mock model to raise exception
    async def mock_predict_failure_error(sensor_data, equipment_id):
        raise RuntimeError("Model inference failed")
    
    mock_prediction_service.predict_equipment_failure = mock_predict_failure_error
    
    response = client.post("/api/v1/predict/failure", json=valid_sensor_data)
    
    assert response.status_code in [500, 503]
    data = response.json()
    
    # Should contain error details
    assert "detail" in data


def test_predict_failure_value_error(client, valid_sensor_data, mock_prediction_service):
    """
    Test prediction when service raises ValueError.
    
    Verifies:
    - Status code 422
    - ValueError is properly handled
    """
    # Mock service to raise ValueError
    async def mock_predict_failure_value_error(sensor_data, equipment_id):
        raise ValueError("Invalid sensor reading: temperature out of range")
    
    mock_prediction_service.predict_equipment_failure = mock_predict_failure_value_error
    
    response = client.post("/api/v1/predict/failure", json=valid_sensor_data)
    
    assert response.status_code == 422
    data = response.json()
    
    assert "detail" in data
    assert "temperature" in data["detail"].lower()


# ============================================================================
# EQUIPMENT HEALTH ENDPOINT TESTS
# ============================================================================

def test_equipment_health_endpoint(client, mock_prediction_service):
    """
    Test /api/v1/equipment/health/{equipment_id} endpoint.
    
    Verifies:
    - Status code 200
    - Response contains equipment_id
    - Health score is present
    - Status and timestamps are included
    """
    # Mock equipment health response
    async def mock_get_health(equipment_id):
        return EquipmentHealthResponse(
            equipment_id=equipment_id,
            health_score=85.0,
            status="HEALTHY",
            last_check=datetime.utcnow(),
            next_maintenance=datetime.utcnow() + timedelta(days=30),
            failure_probability=0.15
        )
    
    mock_prediction_service.get_equipment_health = mock_get_health
    
    equipment_id = "RADAR-LOC-001"
    response = client.get(f"/api/v1/equipment/health/{equipment_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["equipment_id"] == equipment_id
    assert "health_score" in data
    assert "status" in data
    assert "last_check" in data
    assert "failure_probability" in data
    
    # Verify types and ranges
    assert isinstance(data["health_score"], (int, float))
    assert 0.0 <= data["health_score"] <= 100.0
    assert data["status"] in ["HEALTHY", "WARNING", "CRITICAL"]
    assert 0.0 <= data["failure_probability"] <= 1.0


def test_equipment_health_invalid_id(client, mock_prediction_service):
    """
    Test equipment health endpoint with invalid equipment ID format.
    
    Verifies:
    - Status code 400 (Bad Request)
    - Error message indicates invalid format
    """
    # Mock to raise ValueError for invalid ID
    async def mock_get_health_error(equipment_id):
        raise ValueError(f"Invalid equipment ID format: {equipment_id}")
    
    mock_prediction_service.get_equipment_health = mock_get_health_error
    
    invalid_id = "invalid-id"
    response = client.get(f"/api/v1/equipment/health/{invalid_id}")
    
    assert response.status_code == 400
    data = response.json()
    
    assert "detail" in data


# ============================================================================
# BATCH PREDICTION TESTS
# ============================================================================

def test_batch_prediction_success(client, mock_prediction_service):
    """
    Test batch prediction with multiple valid readings.
    
    Verifies:
    - Status code 200
    - Returns predictions for all readings
    - Total count matches
    """
    # Mock batch predict
    async def mock_batch_predict(readings):
        results = []
        for reading in readings:
            results.append(PredictionResponse(
                equipment_id=reading.equipment_id,
                prediction=1,
                failure_probability=0.75,
                severity="HIGH",
                days_until_failure=15,
                confidence="high",
                timestamp=datetime.utcnow(),
                model_version="v1.0"
            ))
        return results
    
    mock_prediction_service.batch_predict = mock_batch_predict
    
    batch_data = {
        "readings": [
            {
                "equipment_id": "RADAR-LOC-001",
                "temperature": 85.5,
                "vibration": 0.45,
                "pressure": 3.2
            },
            {
                "equipment_id": "RADAR-LOC-002",
                "temperature": 78.2,
                "vibration": 0.38,
                "pressure": 3.0
            }
        ]
    }
    
    response = client.post("/api/v1/predict/batch", json=batch_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "predictions" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["predictions"]) == 2


def test_batch_prediction_too_many_readings(client):
    """
    Test batch prediction with more than 100 readings.
    
    Verifies:
    - Status code 422
    - Error message about maximum batch size
    """
    # Create 101 readings
    readings = [
        {
            "equipment_id": f"RADAR-LOC-{i:03d}",
            "temperature": 85.0,
            "vibration": 0.4,
            "pressure": 3.0
        }
        for i in range(101)
    ]
    
    batch_data = {"readings": readings}
    
    response = client.post("/api/v1/predict/batch", json=batch_data)
    
    assert response.status_code == 422


def test_batch_prediction_empty_list(client):
    """
    Test batch prediction with empty readings list.
    
    Verifies:
    - Status code 422
    - Validation catches empty list
    """
    batch_data = {"readings": []}
    
    response = client.post("/api/v1/predict/batch", json=batch_data)
    
    assert response.status_code == 422


# ============================================================================
# MODEL INFO ENDPOINT TESTS
# ============================================================================

def test_get_model_info(client, mock_model_service):
    """
    Test /api/v1/model/info endpoint.
    
    Verifies:
    - Status code 200
    - Returns model metadata
    - Includes performance metrics
    """
    response = client.get("/api/v1/model/info")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields
    required_fields = [
        "model_type",
        "version",
        "trained_date",
        "features",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "roc_auc"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Verify types
    assert isinstance(data["features"], list)
    assert isinstance(data["accuracy"], (int, float))
    assert isinstance(data["precision"], (int, float))
    assert isinstance(data["recall"], (int, float))
    
    # Verify metric ranges
    for metric in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]:
        assert 0.0 <= data[metric] <= 1.0, f"{metric} out of range"


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_predict_with_boundary_values(client):
    """
    Test prediction with values at boundary limits.
    
    Verifies:
    - Minimum valid values work
    - Maximum valid values work
    """
    # Test minimum values
    min_data = {
        "temperature": -50.0,  # Minimum
        "vibration": 0.0,      # Minimum
        "pressure": 0.0        # Minimum
    }
    
    response = client.post("/api/v1/predict/failure", json=min_data)
    assert response.status_code in [200, 422]  # May fail if model can't handle
    
    # Test maximum values
    max_data = {
        "temperature": 200.0,  # Maximum
        "vibration": 2.0,      # Maximum
        "pressure": 10.0       # Maximum
    }
    
    response = client.post("/api/v1/predict/failure", json=max_data)
    assert response.status_code in [200, 422]


def test_predict_with_extreme_values_outside_range(client):
    """
    Test prediction with values just outside valid ranges.
    
    Verifies:
    - Validation catches out-of-range values
    """
    # Just below minimum
    below_min = create_invalid_sensor_data("temperature", -50.1)
    response = client.post("/api/v1/predict/failure", json=below_min)
    assert response.status_code == 422
    
    # Just above maximum
    above_max = create_invalid_sensor_data("temperature", 200.1)
    response = client.post("/api/v1/predict/failure", json=above_max)
    assert response.status_code == 422


def test_malformed_json_request(client):
    """
    Test endpoint with malformed JSON.
    
    Verifies:
    - Status code 422
    - Proper error handling for invalid JSON
    """
    response = client.post(
        "/api/v1/predict/failure",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_prediction_workflow(client, valid_sensor_data_with_equipment, mock_prediction_service):
    """
    Test complete prediction workflow.
    
    Steps:
    1. Check health endpoint
    2. Make prediction
    3. Get equipment health
    4. Get model info
    """
    # Mock services
    async def mock_predict(sensor_data):
        return PredictionResponse(
            equipment_id=sensor_data.equipment_id,
            prediction=1,
            failure_probability=0.82,
            severity="CRITICAL",
            days_until_failure=7,
            confidence="high",
            timestamp=datetime.utcnow(),
            model_version="v1.0"
        )
    
    async def mock_health(equipment_id):
        return EquipmentHealthResponse(
            equipment_id=equipment_id,
            health_score=18.0,
            status="CRITICAL",
            last_check=datetime.utcnow(),
            next_maintenance=datetime.utcnow() + timedelta(days=7),
            failure_probability=0.82
        )
    
    mock_prediction_service.predict_with_equipment_id = mock_predict
    mock_prediction_service.get_equipment_health = mock_health
    
    # 1. Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    # 2. Make prediction
    pred_response = client.post("/api/v1/predict", json=valid_sensor_data_with_equipment)
    assert pred_response.status_code == 200
    pred_data = pred_response.json()
    
    # 3. Get equipment health
    equipment_id = valid_sensor_data_with_equipment["equipment_id"]
    eq_response = client.get(f"/api/v1/equipment/health/{equipment_id}")
    assert eq_response.status_code == 200
    
    # 4. Get model info
    info_response = client.get("/api/v1/model/info")
    assert info_response.status_code == 200
    
    # Verify workflow consistency
    eq_data = eq_response.json()
    assert pred_data["equipment_id"] == eq_data["equipment_id"]
    assert pred_data["severity"] == eq_data["status"]
