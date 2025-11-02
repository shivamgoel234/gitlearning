"""
Tests for Alert & Maintenance Service.

Tests API endpoints, alert creation, and maintenance scheduling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "alert-maintenance"


class TestAlertEndpoints:
    """Test alert endpoints."""
    
    def test_create_alert(self, client):
        """Test alert creation."""
        with patch("app.services.alert_service.create_alert") as mock_create:
            mock_create.return_value = AsyncMock(
                alert_id="alert-123",
                equipment_id="RADAR-LOC-001",
                severity="HIGH",
                message="Test alert",
                failure_probability=0.75,
                acknowledged=False,
                timestamp=datetime.utcnow()
            )
            
            alert_data = {
                "equipment_id": "RADAR-LOC-001",
                "prediction_id": "pred-123",
                "severity": "HIGH",
                "failure_probability": 0.75
            }
            
            response = client.post("/api/v1/alerts", json=alert_data)
            assert response.status_code in [200, 201]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
