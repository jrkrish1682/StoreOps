"""Tests for Reports module."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.reports.models import ReportStatus, ReportType


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


class TestReportsRoutes:
    """Tests for reports routes."""

    def test_create_report(self, client: TestClient) -> None:
        """Test creating report."""
        report_data = {
            "title": "Store Summary Report",
            "report_type": ReportType.STORE_SUMMARY,
        }
        response = client.post("/api/v1/reports", json=report_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Store Summary Report"
        assert data["status"] == ReportStatus.DRAFT

    def test_get_report(self, client: TestClient) -> None:
        """Test getting report."""
        report_data = {
            "title": "Regional Summary",
            "report_type": ReportType.REGIONAL_SUMMARY,
        }
        create_response = client.post("/api/v1/reports", json=report_data)
        report_id = create_response.json()["id"]

        response = client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Regional Summary"

    def test_list_reports(self, client: TestClient) -> None:
        """Test listing reports."""
        for i in range(2):
            report_data = {
                "title": f"Report {i}",
                "report_type": ReportType.DEPARTMENT_PERFORMANCE,
            }
            client.post("/api/v1/reports", json=report_data)

        response = client.get("/api/v1/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_reports_by_type(self, client: TestClient) -> None:
        """Test filtering reports by type."""
        report_data = {
            "title": "Activity Metrics",
            "report_type": ReportType.ACTIVITY_METRICS,
        }
        client.post("/api/v1/reports", json=report_data)

        response = client.get(f"/api/v1/reports/type/{ReportType.ACTIVITY_METRICS}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_update_report(self, client: TestClient) -> None:
        """Test updating report."""
        report_data = {
            "title": "Compliance Report",
            "report_type": ReportType.COMPLIANCE_REPORT,
        }
        create_response = client.post("/api/v1/reports", json=report_data)
        report_id = create_response.json()["id"]

        update_data = {
            "status": ReportStatus.PUBLISHED,
            "description": "Updated report",
        }
        response = client.put(f"/api/v1/reports/{report_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ReportStatus.PUBLISHED

    def test_delete_report(self, client: TestClient) -> None:
        """Test deleting report."""
        report_data = {
            "title": "Report to Delete",
            "report_type": ReportType.STORE_SUMMARY,
        }
        create_response = client.post("/api/v1/reports", json=report_data)
        report_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/reports/{report_id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 404
