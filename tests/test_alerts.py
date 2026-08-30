"""Tests for Alerts module."""

import pytest
from fastapi.testclient import TestClient

from src.alerts.models import AlertSeverity, AlertStatus, AlertType
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


class TestAlertsRoutes:
    """Tests for alerts routes."""

    def test_create_alert(self, client: TestClient) -> None:
        """Test creating alert."""
        alert_data = {
            "title": "SLA Breach",
            "description": "Task overdue",
            "alert_type": AlertType.SLA_BREACH,
            "severity": AlertSeverity.HIGH,
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "SLA Breach"
        assert data["severity"] == AlertSeverity.HIGH

    def test_get_alert(self, client: TestClient) -> None:
        """Test getting alert."""
        alert_data = {
            "title": "Critical Issue",
            "alert_type": AlertType.QUALITY_ISSUE,
            "severity": AlertSeverity.CRITICAL,
        }
        create_response = client.post("/api/v1/alerts", json=alert_data)
        alert_id = create_response.json()["id"]

        response = client.get(f"/api/v1/alerts/{alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Critical Issue"

    def test_list_alerts(self, client: TestClient) -> None:
        """Test listing alerts."""
        for i in range(2):
            alert_data = {
                "title": f"Alert {i}",
                "alert_type": AlertType.TASK_OVERDUE,
                "severity": AlertSeverity.MEDIUM,
            }
            client.post("/api/v1/alerts", json=alert_data)

        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_alerts_by_status(self, client: TestClient) -> None:
        """Test filtering alerts by status."""
        alert_data = {
            "title": "Open Alert",
            "alert_type": AlertType.LOW_INVENTORY,
            "severity": AlertSeverity.LOW,
            "status": AlertStatus.OPEN,
        }
        client.post("/api/v1/alerts", json=alert_data)

        response = client.get(f"/api/v1/alerts/status/{AlertStatus.OPEN}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_alerts_by_severity(self, client: TestClient) -> None:
        """Test filtering alerts by severity."""
        alert_data = {
            "title": "High Severity",
            "alert_type": AlertType.STAFFING_ISSUE,
            "severity": AlertSeverity.HIGH,
        }
        client.post("/api/v1/alerts", json=alert_data)

        response = client.get(f"/api/v1/alerts/severity/{AlertSeverity.HIGH}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_update_alert(self, client: TestClient) -> None:
        """Test updating alert."""
        alert_data = {
            "title": "Alert to Update",
            "alert_type": AlertType.SLA_BREACH,
            "severity": AlertSeverity.HIGH,
        }
        create_response = client.post("/api/v1/alerts", json=alert_data)
        alert_id = create_response.json()["id"]

        update_data = {"status": AlertStatus.RESOLVED}
        response = client.put(f"/api/v1/alerts/{alert_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == AlertStatus.RESOLVED
