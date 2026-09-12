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


class TestActivitiesBulkUpdate:
    """Tests for bulk activity status update."""

    def test_bulk_update_all_succeed(self, client: TestClient) -> None:
        """AC1: All activities successfully updated."""
        # Create 3 activities
        task1_data = {
            "title": "Restock dairy",
            "category": TaskCategory.RESTOCKING,
            "status": TaskStatus.TODO,
        }
        task2_data = {
            "title": "Floor check",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.IN_PROGRESS,
        }
        task3_data = {
            "title": "Compliance review",
            "category": TaskCategory.COMPLIANCE,
            "status": TaskStatus.TODO,
        }

        r1 = client.post("/api/v1/activities/tasks", json=task1_data)
        r2 = client.post("/api/v1/activities/tasks", json=task2_data)
        r3 = client.post("/api/v1/activities/tasks", json=task3_data)

        task1_id = r1.json()["id"]
        task2_id = r2.json()["id"]
        task3_id = r3.json()["id"]

        # Bulk update to DONE
        bulk_data = {
            "activity_ids": [task1_id, task2_id, task3_id],
            "new_status": TaskStatus.DONE,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200
        data = response.json()

        # Verify succeeded
        assert len(data["succeeded"]) == 3
        assert len(data["failed"]) == 0

        # Verify summary
        assert data["summary"]["total"] == 3
        assert data["summary"]["succeeded"] == 3
        assert data["summary"]["failed"] == 0

        # Verify status updated
        for item in data["succeeded"]:
            assert item["status"] == TaskStatus.DONE
            assert "updated_at" in item

    def test_bulk_update_partial_success(self, client: TestClient) -> None:
        """AC2: Partial success with mixed outcomes."""
        # Create activity-1 (TODO) and activity-2 (DONE)
        task1_data = {
            "title": "Restock dairy",
            "category": TaskCategory.RESTOCKING,
            "status": TaskStatus.TODO,
        }
        task2_data = {
            "title": "Floor check",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.DONE,
        }

        r1 = client.post("/api/v1/activities/tasks", json=task1_data)
        r2 = client.post("/api/v1/activities/tasks", json=task2_data)

        task1_id = r1.json()["id"]
        task2_id = r2.json()["id"]

        # Bulk update with non-existent activity-99
        bulk_data = {
            "activity_ids": [task1_id, task2_id, "activity-99"],
            "new_status": TaskStatus.BLOCKED,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200
        data = response.json()

        # Verify partial success
        assert len(data["succeeded"]) == 1
        assert len(data["failed"]) == 2

        # Verify succeeded item
        assert data["succeeded"][0]["id"] == task1_id
        assert data["succeeded"][0]["status"] == TaskStatus.BLOCKED

        # Verify failed items
        failed_ids = [item["activity_id"] for item in data["failed"]]
        assert task2_id in failed_ids
        assert "activity-99" in failed_ids

        # Verify error codes
        business_rule_violations = [
            item for item in data["failed"] if item["activity_id"] == task2_id
        ]
        assert len(business_rule_violations) == 1
        assert business_rule_violations[0]["error_code"] == "BUSINESS_RULE_VIOLATION"

        not_founds = [
            item for item in data["failed"] if item["activity_id"] == "activity-99"
        ]
        assert len(not_founds) == 1
        assert not_founds[0]["error_code"] == "NOT_FOUND"

        # Verify summary
        assert data["summary"]["total"] == 3
        assert data["summary"]["succeeded"] == 1
        assert data["summary"]["failed"] == 2

    def test_bulk_update_empty_activity_list(self, client: TestClient) -> None:
        """AC3: Validation failure with empty activity list."""
        bulk_data = {
            "activity_ids": [],
            "new_status": TaskStatus.DONE,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 422  # ValidationError returns 422
        data = response.json()
        assert data["detail"]["error_code"] == "VALIDATION_ERROR"
        assert "activity_ids" in data["detail"]["message"].lower()

    def test_bulk_update_invalid_status_enum(self, client: TestClient) -> None:
        """AC4: Validation failure with invalid status enum."""
        bulk_data = {
            "activity_ids": ["task_1"],
            "new_status": "INVALID_STATUS",
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 422
        data = response.json()
        # When validation happens in service, error_code is in detail dict
        assert data["detail"]["error_code"] == "VALIDATION_ERROR"
        assert "new_status" in data["detail"]["message"].lower()

    def test_bulk_update_too_many_activities(self, client: TestClient) -> None:
        """AC5: Validation failure with too many activities (>100)."""
        # Create 101 activity IDs
        activity_ids = [f"task_{i}" for i in range(101)]
        bulk_data = {
            "activity_ids": activity_ids,
            "new_status": TaskStatus.DONE,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 422  # ValidationError returns 422
        data = response.json()
        assert data["detail"]["error_code"] == "VALIDATION_ERROR"
        assert "100" in data["detail"]["message"]

    def test_bulk_update_activity_not_found(self, client: TestClient) -> None:
        """AC2 edge case: Non-existent activity."""
        bulk_data = {
            "activity_ids": ["activity-99"],
            "new_status": TaskStatus.TODO,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["succeeded"]) == 0
        assert len(data["failed"]) == 1
        assert data["failed"][0]["activity_id"] == "activity-99"
        assert data["failed"][0]["error_code"] == "NOT_FOUND"

    def test_bulk_update_business_rule_violation(self, client: TestClient) -> None:
        """AC2 edge case: Invalid status transition."""
        # Create activity with status DONE
        task_data = {
            "title": "Completed task",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.DONE,
        }
        r = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = r.json()["id"]

        # Try to transition to BLOCKED (invalid from DONE)
        bulk_data = {
            "activity_ids": [task_id],
            "new_status": TaskStatus.BLOCKED,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["succeeded"]) == 0
        assert len(data["failed"]) == 1
        assert data["failed"][0]["activity_id"] == task_id
        assert data["failed"][0]["error_code"] == "BUSINESS_RULE_VIOLATION"

    def test_bulk_update_single_activity(self, client: TestClient) -> None:
        """AC1 edge case: Single activity update."""
        # Create 1 activity
        task_data = {
            "title": "Single task",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.TODO,
        }
        r = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = r.json()["id"]

        # Bulk update single activity
        bulk_data = {
            "activity_ids": [task_id],
            "new_status": TaskStatus.DONE,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["succeeded"]) == 1
        assert len(data["failed"]) == 0
        assert data["summary"]["total"] == 1
        assert data["summary"]["succeeded"] == 1
        assert data["summary"]["failed"] == 0

    def test_bulk_update_idempotent(self, client: TestClient) -> None:
        """Determinism test: Idempotent behavior."""
        # Create 2 activities
        task1_data = {
            "title": "Task 1",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.TODO,
        }
        task2_data = {
            "title": "Task 2",
            "category": TaskCategory.COMPLIANCE,
            "status": TaskStatus.TODO,
        }
        r1 = client.post("/api/v1/activities/tasks", json=task1_data)
        r2 = client.post("/api/v1/activities/tasks", json=task2_data)
        task1_id = r1.json()["id"]
        task2_id = r2.json()["id"]

        # First update
        bulk_data = {
            "activity_ids": [task1_id, task2_id],
            "new_status": TaskStatus.DONE,
        }
        response1 = client.patch("/api/v1/activities/bulk-status", json=bulk_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["succeeded"]) == 2
        assert len(data1["failed"]) == 0

        # Second update (same request) - should fail for both
        response2 = client.patch("/api/v1/activities/bulk-status", json=bulk_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["succeeded"]) == 0
        assert len(data2["failed"]) == 2
        assert data2["failed"][0]["error_code"] == "BUSINESS_RULE_VIOLATION"
        assert data2["failed"][1]["error_code"] == "BUSINESS_RULE_VIOLATION"

    def test_bulk_update_response_format(self, client: TestClient) -> None:
        """Contract compliance: Response format."""
        # Create activity
        task_data = {
            "title": "Format test",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.TODO,
        }
        r = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = r.json()["id"]

        # Bulk update
        bulk_data = {
            "activity_ids": [task_id],
            "new_status": TaskStatus.IN_PROGRESS,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "succeeded" in data
        assert "failed" in data
        assert "summary" in data

        # Verify succeeded items have full Task fields
        assert len(data["succeeded"]) == 1
        succeeded_item = data["succeeded"][0]
        assert "id" in succeeded_item
        assert "status" in succeeded_item
        assert "updated_at" in succeeded_item
        assert "title" in succeeded_item

        # Verify failed items have error fields
        assert isinstance(data["failed"], list)

        # Verify summary has correct fields
        summary = data["summary"]
        assert "total" in summary
        assert "succeeded" in summary
        assert "failed" in summary
        assert summary["total"] == summary["succeeded"] + summary["failed"]

    def test_bulk_update_shift_handover_audit_context(
        self, client: TestClient
    ) -> None:
        """Shift-specific: Audit context in activity logs."""
        from src.activities.repository import get_activities_repository
        from src.activities.service import get_activities_service

        # Create 2 activities
        task1_data = {
            "title": "Task 1",
            "category": TaskCategory.OPERATIONAL,
            "status": TaskStatus.TODO,
        }
        task2_data = {
            "title": "Task 2",
            "category": TaskCategory.COMPLIANCE,
            "status": TaskStatus.TODO,
        }
        r1 = client.post("/api/v1/activities/tasks", json=task1_data)
        r2 = client.post("/api/v1/activities/tasks", json=task2_data)
        task1_id = r1.json()["id"]
        task2_id = r2.json()["id"]

        # Bulk update
        bulk_data = {
            "activity_ids": [task1_id, task2_id],
            "new_status": TaskStatus.DONE,
        }
        response = client.patch("/api/v1/activities/bulk-status", json=bulk_data)

        assert response.status_code == 200

        # Verify activity logs have shift_handover context
        repo = get_activities_repository()
        if hasattr(repo, "_activity_logs"):
            logs = repo._activity_logs
            assert len(logs) >= 2

            for log in logs[-2:]:  # Last 2 entries
                assert log["action"] == "status_changed"
                assert log["details"]["context"] == "shift_handover"
                assert log["details"]["bulk_update"] is True
