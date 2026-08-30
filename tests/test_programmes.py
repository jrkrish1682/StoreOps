"""Tests for Programmes module."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.programmes.models import ProgrammeStatus, ProgrammeType


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


class TestProgrammesRoutes:
    """Tests for programmes routes."""

    def test_create_programme(self, client: TestClient) -> None:
        """Test creating a programme."""
        programme_data = {
            "name": "Q4 Campaign",
            "description": "Q4 promotional campaign",
            "programme_type": ProgrammeType.CAMPAIGN,
        }
        response = client.post("/api/v1/programmes", json=programme_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Q4 Campaign"
        assert data["programme_type"] == ProgrammeType.CAMPAIGN
        assert data["status"] == ProgrammeStatus.DRAFT

    def test_get_programme(self, client: TestClient) -> None:
        """Test getting a programme."""
        # Create programme
        programme_data = {
            "name": "Store Initiative",
            "programme_type": ProgrammeType.INITIATIVE,
        }
        create_response = client.post("/api/v1/programmes", json=programme_data)
        programme_id = create_response.json()["id"]

        # Get programme
        response = client.get(f"/api/v1/programmes/{programme_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == programme_id
        assert data["name"] == "Store Initiative"

    def test_list_programmes(self, client: TestClient) -> None:
        """Test listing programmes."""
        # Create programmes
        for i in range(2):
            programme_data = {
                "name": f"Programme {i}",
                "programme_type": ProgrammeType.ROLLOUT,
            }
            client.post("/api/v1/programmes", json=programme_data)

        # List programmes
        response = client.get("/api/v1/programmes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_update_programme(self, client: TestClient) -> None:
        """Test updating a programme."""
        # Create programme
        programme_data = {
            "name": "Original Name",
            "programme_type": ProgrammeType.INITIATIVE,
        }
        create_response = client.post("/api/v1/programmes", json=programme_data)
        programme_id = create_response.json()["id"]

        # Update programme
        update_data = {
            "name": "Updated Name",
            "status": ProgrammeStatus.ACTIVE,
        }
        response = client.put(f"/api/v1/programmes/{programme_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["status"] == ProgrammeStatus.ACTIVE

    def test_delete_programme(self, client: TestClient) -> None:
        """Test deleting a programme."""
        # Create programme
        programme_data = {
            "name": "Programme to Delete",
            "programme_type": ProgrammeType.CAMPAIGN,
        }
        create_response = client.post("/api/v1/programmes", json=programme_data)
        programme_id = create_response.json()["id"]

        # Delete programme
        response = client.delete(f"/api/v1/programmes/{programme_id}")
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/v1/programmes/{programme_id}")
        assert response.status_code == 404
