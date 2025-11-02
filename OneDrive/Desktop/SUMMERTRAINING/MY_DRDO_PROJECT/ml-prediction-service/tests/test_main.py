"""
Tests for ML Prediction Service.

Tests API endpoints, model inference, and business logic.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import numpy as np

from app.main import app
from app.models import PredictionRequest


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_prediction_request():
    """Valid prediction request data."""
    return {
        "equipment_id": "RADAR-LOC-001",
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0
    }


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ml-prediction"
        assert "timestamp" in data


class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    def test_predict_failure_valid_request(self, client, valid_prediction_request):
        """Test successful failure prediction."""
        with patch("app.services.ml_service.predict_failure") as mock_predict:
            mock_predict.return_value = AsyncMock(
                prediction_id="pred-123",
                equipment_id="RADAR-LOC-001",
                failure_probability=0.75,
                severity="HIGH",
                health_score=35.5,
                days_until_failure=15,
                confidence="high",
                timestamp=datetime.utcnow()
            )
            
            response = client.post("/api/v1/predict/failure", json=valid_prediction_request)
            assert response.status_code in [200, 201]
    
    def test_predict_failure_invalid_equipment_id(self, client, valid_prediction_request):
        """Test validation error for invalid equipment ID."""
        invalid_data = valid_prediction_request.copy()
        invalid_data["equipment_id"] = "invalid"
        
        response = client.post("/api/v1/predict/failure", json=invalid_data)
        assert response.status_code == 422
    
    def test_predict_failure_out_of_range_temperature(self, client, valid_prediction_request):
        """Test validation error for out of range temperature."""
        invalid_data = valid_prediction_request.copy()
        invalid_data["temperature"] = 999.0
        
        response = client.post("/api/v1/predict/failure", json=invalid_data)
        assert response.status_code == 422


class TestPredictionModel:
    """Test Pydantic model validation."""
    
    def test_equipment_id_normalization(self):
        """Test equipment ID is normalized to uppercase."""
        data = {
            "equipment_id": "radar-loc-001",
            "temperature": 85.5,
            "vibration": 0.45,
            "pressure": 3.2
        }
        request = PredictionRequest(**data)
        assert request.equipment_id == "RADAR-LOC-001"
    
    def test_optional_fields_default_values(self):
        """Test optional fields have default values."""
        request = PredictionRequest(
            equipment_id="RADAR-LOC-001",
            temperature=85.5,
            vibration=0.45,
            pressure=3.2
        )
        assert request.humidity == 0.0
        assert request.voltage == 0.0


class TestMLService:
    """Test ML service business logic."""
    
    def test_mock_model_prediction(self):
        """Test mock model generates predictions."""
        from app.services import MockModel
        
        model = MockModel()
        features = np.array([[85.5, 0.45, 3.2, 65.0, 220.0]])
        
        probabilities = model.predict_proba(features)
        
        assert probabilities.shape == (1, 2)
        assert 0 <= probabilities[0][1] <= 1
        assert abs(probabilities[0][0] + probabilities[0][1] - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
