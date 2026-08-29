"""Tests for Staff module."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.staff.models import StaffRole, StaffStatus


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


class TestStaffRoutes:
    """Tests for staff routes."""

    def test_create_staff(self, client: TestClient) -> None:
        """Test creating staff member."""
        staff_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "role": StaffRole.STORE_MANAGER,
        }
        response = client.post("/api/v1/staff", json=staff_data)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["role"] == StaffRole.STORE_MANAGER

    def test_get_staff(self, client: TestClient) -> None:
        """Test getting staff member."""
        staff_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "role": StaffRole.DEPARTMENT_LEAD,
        }
        create_response = client.post("/api/v1/staff", json=staff_data)
        staff_id = create_response.json()["id"]

        response = client.get(f"/api/v1/staff/{staff_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"

    def test_list_staff(self, client: TestClient) -> None:
        """Test listing staff."""
        for i in range(2):
            staff_data = {
                "first_name": f"Staff{i}",
                "last_name": "Member",
                "email": f"staff{i}@example.com",
                "role": StaffRole.STAFF_MEMBER,
            }
            client.post("/api/v1/staff", json=staff_data)

        response = client.get("/api/v1/staff")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_update_staff(self, client: TestClient) -> None:
        """Test updating staff member."""
        staff_data = {
            "first_name": "Bob",
            "last_name": "Wilson",
            "email": "bob.wilson@example.com",
            "role": StaffRole.STAFF_MEMBER,
        }
        create_response = client.post("/api/v1/staff", json=staff_data)
        staff_id = create_response.json()["id"]

        update_data = {
            "role": StaffRole.DEPARTMENT_LEAD,
            "status": StaffStatus.INACTIVE,
        }
        response = client.put(f"/api/v1/staff/{staff_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == StaffRole.DEPARTMENT_LEAD

    def test_delete_staff(self, client: TestClient) -> None:
        """Test deleting staff member."""
        staff_data = {
            "first_name": "Alice",
            "last_name": "Brown",
            "email": "alice.brown@example.com",
            "role": StaffRole.STAFF_MEMBER,
        }
        create_response = client.post("/api/v1/staff", json=staff_data)
        staff_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/staff/{staff_id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/staff/{staff_id}")
        assert response.status_code == 404

    def test_duplicate_email(self, client: TestClient) -> None:
        """Test duplicate email validation."""
        staff_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "duplicate@example.com",
            "role": StaffRole.STAFF_MEMBER,
        }
        # Create first staff member
        response1 = client.post("/api/v1/staff", json=staff_data)
        assert response1.status_code == 201

        # Try to create another with same email
        staff_data["first_name"] = "Jane"
        response2 = client.post("/api/v1/staff", json=staff_data)
        assert response2.status_code == 409
