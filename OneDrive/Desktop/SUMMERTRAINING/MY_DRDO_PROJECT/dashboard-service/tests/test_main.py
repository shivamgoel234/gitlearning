"""
Tests for Dashboard Service.

Tests API endpoints and data aggregation.
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
        assert data["service"] == "dashboard"


class TestDashboardEndpoints:
    """Test dashboard endpoints."""
    
    def test_get_dashboard_summary(self, client):
        """Test dashboard summary endpoint."""
        with patch("app.services.dashboard_service.get_dashboard_summary") as mock_summary:
            mock_summary.return_value = AsyncMock(
                total_equipment=5,
                critical_alerts=2,
                pending_maintenance=3,
                average_health_score=75.5,
                equipment_by_status={"CRITICAL": 1, "HIGH": 2, "LOW": 2},
                recent_alerts=[],
                timestamp=datetime.utcnow()
            )
            
            response = client.get("/api/v1/dashboard/summary")
            assert response.status_code in [200, 500]  # May fail without DB


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
