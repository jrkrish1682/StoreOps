"""Tests for Activities module."""

import pytest
from fastapi.testclient import TestClient

from src.activities.models import TaskCategory, TaskPriority, TaskStatus
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


class TestActivitiesRoutes:
    """Tests for activities routes."""

    def test_create_task(self, client: TestClient) -> None:
        """Test creating a task."""
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        response = client.post("/api/v1/activities/tasks", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["status"] == TaskStatus.TODO
        assert "id" in data

    def test_get_task(self, client: TestClient) -> None:
        """Test getting a task."""
        # Create task
        task_data = {
            "title": "Test Task",
            "priority": TaskPriority.MEDIUM,
            "category": TaskCategory.COMPLIANCE,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Get task
        response = client.get(f"/api/v1/activities/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"

    def test_list_tasks(self, client: TestClient) -> None:
        """Test listing tasks."""
        # Create multiple tasks
        for i in range(3):
            task_data = {
                "title": f"Task {i}",
                "priority": TaskPriority.LOW,
                "category": TaskCategory.RESTOCKING,
            }
            client.post("/api/v1/activities/tasks", json=task_data)

        # List tasks
        response = client.get("/api/v1/activities/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_update_task(self, client: TestClient) -> None:
        """Test updating a task."""
        # Create task
        task_data = {
            "title": "Original Title",
            "priority": TaskPriority.MEDIUM,
            "category": TaskCategory.PLANOGRAM,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Update task
        update_data = {"title": "Updated Title", "status": TaskStatus.IN_PROGRESS}
        response = client.put(f"/api/v1/activities/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == TaskStatus.IN_PROGRESS

    def test_delete_task(self, client: TestClient) -> None:
        """Test deleting a task."""
        # Create task
        task_data = {
            "title": "Task to Delete",
            "priority": TaskPriority.LOW,
            "category": TaskCategory.MAINTENANCE,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Delete task
        response = client.delete(f"/api/v1/activities/tasks/{task_id}")
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/v1/activities/tasks/{task_id}")
        assert response.status_code == 404

    def test_get_tasks_by_status(self, client: TestClient) -> None:
        """Test filtering tasks by status."""
        # Create tasks with different statuses
        for status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.TODO]:
            task_data = {
                "title": f"Task {status}",
                "status": status,
                "priority": TaskPriority.MEDIUM,
                "category": TaskCategory.OPERATIONAL,
            }
            client.post("/api/v1/activities/tasks", json=task_data)

        # Filter by TODO status
        response = client.get(f"/api/v1/activities/tasks/status/{TaskStatus.TODO}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_create_task_validation(self, client: TestClient) -> None:
        """Test task creation validation."""
        # Missing required fields
        task_data = {
            "description": "Missing title",
        }
        response = client.post("/api/v1/activities/tasks", json=task_data)
        assert response.status_code == 422

    def test_get_nonexistent_task(self, client: TestClient) -> None:
        """Test getting non-existent task."""
        response = client.get("/api/v1/activities/tasks/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "NOT_FOUND"
