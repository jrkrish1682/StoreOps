# StoreOps Testing Guide

**Version:** 1.0.0  
**Last Updated:** 2026-08-29  
**Scope:** Testing conventions and patterns for StoreOps

---

## Purpose

This skill documents how to test StoreOps features effectively. It covers:
- Existing pytest structure
- TestClient (HTTPX) usage
- Route testing patterns
- Service testing
- Error path testing
- EventBus verification
- Acceptance criteria traceability

**Important:** Testing only HTTP status codes is insufficient. Every acceptance criterion must be validated by at least one test.

**Use this skill when:**
- Writing tests for new features
- Adding acceptance criteria verification
- Testing error cases
- Verifying cross-module event publishing

---

## 1. Test Framework Setup

### Framework: Pytest + pytest-asyncio

**Dependencies:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
```

**Configuration:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
asyncio_mode = "auto"
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_activities.py

# Run specific test
pytest tests/test_activities.py::TestActivitiesRoutes::test_create_task

# Run with coverage
pytest --cov=src tests/

# Run with verbose output
pytest -vv tests/
```

### Type Check & Lint

```bash
# Type checking (must pass)
mypy src

# Linting (must pass)
ruff check src

# Format code
ruff format src
```

---

## 2. Shared Fixtures (conftest.py)

### Purpose

The `conftest.py` file provides shared fixtures for all tests. Most important is `reset_state`, which prevents test pollution.

**File:** `tests/conftest.py`

```python
"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.activities.repository import get_activities_repository
from src.alerts.repository import get_alerts_repository
from src.main import app
from src.programmes.repository import get_programmes_repository
from src.reports.repository import get_reports_repository
from src.shared.event_bus import reset_event_bus
from src.staff.repository import get_staff_repository


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset all repositories and event bus before each test."""
    # Reset event bus
    reset_event_bus()

    # Reset all repositories to prevent test pollution
    get_activities_repository().reset()
    get_programmes_repository().reset()
    get_staff_repository().reset()
    get_alerts_repository().reset()
    get_reports_repository().reset()

    yield

    # Clean up after test
    reset_event_bus()
    get_activities_repository().reset()
    get_programmes_repository().reset()
    get_staff_repository().reset()
    get_alerts_repository().reset()
    get_reports_repository().reset()
```

### Key Points

- **`autouse=True`:** Fixture runs before every test automatically
- **`yield`:** Separates setup (before) from cleanup (after)
- **Order matters:** Reset all modules in consistent order

---

## 3. Route Testing Pattern: Full Integration

### When to Use

Test the full stack: HTTP request → Route → Service → Repository → Response

### Skeleton: CREATE (Happy Path)

**File:** `tests/test_activities.py`

```python
"""Tests for Activities module."""

import pytest
from fastapi.testclient import TestClient

from src.activities.models import TaskCategory, TaskPriority, TaskStatus


class TestActivitiesRoutes:
    """Tests for activities routes."""

    def test_create_task(self, client: TestClient) -> None:
        """Happy path: Task creation succeeds.
        
        Acceptance Criteria:
        - POST /api/v1/activities/tasks returns 201
        - Response contains id, title, status, created_at
        """
        # Arrange
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        
        # Act
        response = client.post("/api/v1/activities/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["status"] == TaskStatus.TODO
        assert data["priority"] == TaskPriority.HIGH
        assert data["category"] == TaskCategory.OPERATIONAL
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
```

### Skeleton: READ (GET by ID)

```python
class TestActivitiesRoutes:
    def test_get_task(self, client: TestClient) -> None:
        """Happy path: Get existing task.
        
        Acceptance Criteria:
        - GET /api/v1/activities/tasks/{id} returns 200
        - Response contains correct task data
        """
        # Arrange: Create task
        task_data = {
            "title": "Test Task",
            "priority": TaskPriority.MEDIUM,
            "category": TaskCategory.COMPLIANCE,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Act
        response = client.get(f"/api/v1/activities/tasks/{task_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"
```

### Skeleton: LIST (Pagination)

```python
class TestActivitiesRoutes:
    def test_list_tasks(self, client: TestClient) -> None:
        """Happy path: List tasks with pagination.
        
        Acceptance Criteria:
        - GET /api/v1/activities/tasks returns 200
        - Response contains items array, total, skip, limit
        - Pagination limits items correctly
        """
        # Arrange: Create multiple tasks
        for i in range(3):
            task_data = {
                "title": f"Task {i}",
                "priority": TaskPriority.LOW,
                "category": TaskCategory.RESTOCKING,
            }
            client.post("/api/v1/activities/tasks", json=task_data)
        
        # Act
        response = client.get("/api/v1/activities/tasks")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["skip"] == 0
        assert data["limit"] == 10
```

### Skeleton: UPDATE (PUT)

```python
class TestActivitiesRoutes:
    def test_update_task(self, client: TestClient) -> None:
        """Happy path: Update existing task.
        
        Acceptance Criteria:
        - PUT /api/v1/activities/tasks/{id} returns 200
        - Response contains updated values
        """
        # Arrange: Create task
        task_data = {
            "title": "Original Title",
            "priority": TaskPriority.MEDIUM,
            "category": TaskCategory.PLANOGRAM,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Act
        update_data = {"title": "Updated Title", "status": TaskStatus.IN_PROGRESS}
        response = client.put(
            f"/api/v1/activities/tasks/{task_id}",
            json=update_data,
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == TaskStatus.IN_PROGRESS
```

### Skeleton: DELETE

```python
class TestActivitiesRoutes:
    def test_delete_task(self, client: TestClient) -> None:
        """Happy path: Delete existing task.
        
        Acceptance Criteria:
        - DELETE /api/v1/activities/tasks/{id} returns 204
        - Task no longer exists after deletion
        """
        # Arrange: Create task
        task_data = {
            "title": "Task to Delete",
            "priority": TaskPriority.LOW,
            "category": TaskCategory.MAINTENANCE,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Act: Delete
        response = client.delete(f"/api/v1/activities/tasks/{task_id}")
        
        # Assert: Deletion succeeds
        assert response.status_code == 204
        
        # Verify task is gone
        response = client.get(f"/api/v1/activities/tasks/{task_id}")
        assert response.status_code == 404
```

---

## 4. Error Path Testing

### Validation Error (422)

**Acceptance Criterion:** Invalid input is rejected with 422 and error_code

```python
class TestActivitiesRoutes:
    def test_create_task_missing_title(self, client: TestClient) -> None:
        """Error: Missing required field.
        
        Acceptance Criteria:
        - POST with empty title returns 422
        - Response has error_code VALIDATION_ERROR
        """
        # Arrange
        task_data = {
            "title": "",  # Empty!
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        
        # Act
        response = client.post("/api/v1/activities/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error_code" in data["detail"] or "errors" in data
```

### Not Found Error (404)

**Acceptance Criterion:** Nonexistent resource returns 404 with proper error

```python
class TestActivitiesRoutes:
    def test_get_nonexistent_task(self, client: TestClient) -> None:
        """Error: Resource not found.
        
        Acceptance Criteria:
        - GET /tasks/nonexistent returns 404
        - Response has error_code NOT_FOUND
        """
        # Act
        response = client.get("/api/v1/activities/tasks/nonexistent")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "NOT_FOUND"
        assert "nonexistent" in data["detail"]["message"]
```

### Conflict Error (409)

**Acceptance Criterion:** Duplicate resource is rejected

```python
class TestStaffRoutes:
    def test_create_duplicate_staff(self, client: TestClient) -> None:
        """Error: Duplicate staff email.
        
        Acceptance Criteria:
        - Second POST with same email returns 409
        - Response has error_code CONFLICT
        """
        # Arrange: Create staff
        staff_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "MANAGER",
        }
        client.post("/api/v1/staff/members", json=staff_data)
        
        # Act: Try to create duplicate
        response = client.post("/api/v1/staff/members", json=staff_data)
        
        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error_code"] == "CONFLICT"
```

### Business Rule Violation (400)

**Acceptance Criterion:** Business rules are enforced

```python
class TestActivitiesRoutes:
    def test_cannot_move_completed_task_to_todo(
        self,
        client: TestClient,
    ) -> None:
        """Error: Business rule prevents state transition.
        
        Acceptance Criteria:
        - Cannot move DONE task back to TODO
        - Returns 400 with error_code BUSINESS_RULE_VIOLATION
        """
        # Arrange: Create and complete task
        task_data = {
            "title": "Test Task",
            "priority": TaskPriority.MEDIUM,
            "category": TaskCategory.OPERATIONAL,
        }
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Complete task
        client.put(
            f"/api/v1/activities/tasks/{task_id}",
            json={"status": TaskStatus.DONE},
        )
        
        # Act: Try invalid transition
        response = client.put(
            f"/api/v1/activities/tasks/{task_id}",
            json={"status": TaskStatus.TODO},
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_code"] == "BUSINESS_RULE_VIOLATION"
```

---

## 5. Service Layer Testing

### When to Use

Unit test service methods directly (without HTTP layer). Useful for complex business logic.

### Skeleton: Service Test

```python
"""Tests for Activities service."""

import pytest

from src.activities.models import TaskCategory, TaskCreate, TaskPriority, TaskStatus
from src.activities.service import get_activities_service
from src.shared.errors import NotFoundError, ValidationError


class TestActivitiesService:
    """Tests for activities service logic."""

    @pytest.mark.asyncio
    async def test_create_task_validation(self) -> None:
        """Service validates task creation.
        
        Acceptance Criteria:
        - Empty title raises ValidationError
        - Error message is clear
        """
        service = await get_activities_service()
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.create_task(
                task_create=TaskCreate(
                    title="",  # Empty
                    category=TaskCategory.OPERATIONAL,
                ),
            )
        
        assert "title is required" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_raises_not_found(self) -> None:
        """Service raises NotFoundError for missing task.
        
        Acceptance Criteria:
        - get_task raises NotFoundError
        - Error contains task_id
        """
        service = await get_activities_service()
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_task(task_id="nonexistent")
        
        assert "nonexistent" in exc_info.value.details["resource_id"]
```

---

## 6. EventBus Testing

### Verify Events Published

**Acceptance Criterion:** Events are published with correct payload

```python
from src.shared.event_bus import EventType, get_event_bus


class TestActivitiesRoutes:
    def test_task_creation_publishes_event(self, client: TestClient) -> None:
        """Event: Task creation publishes TASK_CREATED.
        
        Acceptance Criteria:
        - TASK_CREATED event published on creation
        - Event payload contains task_id, title, priority
        """
        # Arrange
        task_data = {
            "title": "Test Task",
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        
        # Act
        response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = response.json()["id"]
        
        # Assert: Event published
        event_bus = get_event_bus()
        history = event_bus.get_event_history()
        
        assert len(history) == 1
        event_type, payload = history[0]
        assert event_type == EventType.TASK_CREATED
        assert payload["task_id"] == task_id
        assert payload["title"] == "Test Task"
        assert payload["priority"] == TaskPriority.HIGH
```

### Verify Event Handlers

**Acceptance Criterion:** Other modules react to events correctly

```python
@pytest.mark.asyncio
async def test_alerts_created_for_critical_tasks(
    client: TestClient,
) -> None:
    """Cross-module: Alerts subscribes to TASK_CREATED.
    
    Acceptance Criteria:
    - When critical task created, alert is created
    - Alert references task_id
    """
    # This test would verify that alerts service subscribes to task events
    # and creates alerts for critical tasks
    
    # Arrange
    task_data = {
        "title": "Critical Task",
        "priority": TaskPriority.CRITICAL,
        "category": TaskCategory.COMPLIANCE,
    }
    
    # Act
    response = client.post("/api/v1/activities/tasks", json=task_data)
    task_id = response.json()["id"]
    
    # Assert: Alert created
    alerts_response = client.get("/api/v1/alerts/alerts")
    alerts = alerts_response.json()["items"]
    
    assert len(alerts) > 0
    alert = alerts[0]
    assert alert["task_id"] == task_id or "critical" in alert["message"].lower()
```

---

## 7. Acceptance Criteria Traceability

### Rule: Every Acceptance Criterion Must Be Tested

**Step 1: List Acceptance Criteria**

```python
"""
Feature: Create Task
Acceptance Criteria:
1. POST /api/v1/activities/tasks with valid data returns 201
2. Response contains id, title, status, priority, category, created_at, updated_at
3. Task stored in repository with correct fields
4. TASK_CREATED event published with task_id, title, priority
5. Empty title raises 422 ValidationError
6. Missing category field raises 422
"""
```

**Step 2: Map to Tests**

```python
class TestActivitiesCreateTask:
    def test_create_task_returns_201(self, client):
        """AC#1: Valid POST returns 201"""
        pass
    
    def test_create_task_response_contains_required_fields(self, client):
        """AC#2: Response has all required fields"""
        pass
    
    def test_create_task_stored_in_repository(self, client):
        """AC#3: Task persisted correctly"""
        pass
    
    def test_create_task_publishes_event(self, client):
        """AC#4: TASK_CREATED event published"""
        pass
    
    def test_create_task_empty_title_validation(self, client):
        """AC#5: Empty title rejected"""
        pass
    
    def test_create_task_missing_category_validation(self, client):
        """AC#6: Missing category rejected"""
        pass
```

---

## 8. Async Test Syntax

### Using `@pytest.mark.asyncio`

```python
import pytest


class TestActivitiesService:
    @pytest.mark.asyncio
    async def test_async_service_method(self) -> None:
        """Service method test with async."""
        service = await get_activities_service()
        
        # Await async calls
        task = await service.get_task("task_1")
        assert task is not None
```

### Key Rules

1. **Decorator required:** `@pytest.mark.asyncio` for async tests
2. **Async function:** `async def test_*`
3. **Await I/O:** `await service.method()`
4. **No await for sync:** `client.get(...)` is sync (TestClient)

---

## 9. Common Test Patterns

### Pattern: Create, Retrieve, Verify

```python
def test_task_create_and_retrieve(self, client: TestClient) -> None:
    """Create task, retrieve it, verify data.
    
    Acceptance Criteria:
    - Created task can be retrieved
    - Retrieved data matches created data
    """
    # Create
    task_data = {
        "title": "Test Task",
        "priority": TaskPriority.HIGH,
        "category": TaskCategory.OPERATIONAL,
    }
    create_response = client.post("/api/v1/activities/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Retrieve
    get_response = client.get(f"/api/v1/activities/tasks/{task_id}")
    retrieved = get_response.json()
    
    # Verify
    assert retrieved["title"] == task_data["title"]
    assert retrieved["priority"] == task_data["priority"]
    assert retrieved["category"] == task_data["category"]
```

### Pattern: List and Filter

```python
def test_list_tasks_by_status_filter(self, client: TestClient) -> None:
    """Create tasks with different statuses, filter by status.
    
    Acceptance Criteria:
    - Filtering by status returns only matching tasks
    - Total count is correct
    """
    # Create tasks with different statuses
    for status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.TODO]:
        task_data = {
            "title": f"Task {status}",
            "status": status,
            "priority": TaskPriority.MEDIUM,
            "category": TaskCategory.OPERATIONAL,
        }
        client.post("/api/v1/activities/tasks", json=task_data)
    
    # Filter by TODO
    response = client.get(f"/api/v1/activities/tasks/status/{TaskStatus.TODO}")
    data = response.json()
    
    # Verify
    assert data["total"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["status"] == TaskStatus.TODO
```

### Pattern: Pagination

```python
def test_pagination(self, client: TestClient) -> None:
    """Verify pagination limits and skip.
    
    Acceptance Criteria:
    - skip parameter skips correct number
    - limit parameter limits correct number
    - total count is accurate
    """
    # Create 15 tasks
    for i in range(15):
        task_data = {
            "title": f"Task {i}",
            "priority": TaskPriority.LOW,
            "category": TaskCategory.OPERATIONAL,
        }
        client.post("/api/v1/activities/tasks", json=task_data)
    
    # Page 1: skip=0, limit=10
    response1 = client.get("/api/v1/activities/tasks?skip=0&limit=10")
    data1 = response1.json()
    assert data1["total"] == 15
    assert len(data1["items"]) == 10
    
    # Page 2: skip=10, limit=10
    response2 = client.get("/api/v1/activities/tasks?skip=10&limit=10")
    data2 = response2.json()
    assert data2["total"] == 15
    assert len(data2["items"]) == 5
```

---

## 10. Running Tests

### Commands

```bash
# Run all tests
pytest

# Run single file
pytest tests/test_activities.py

# Run single test
pytest tests/test_activities.py::TestActivitiesRoutes::test_create_task

# Run tests matching pattern
pytest -k "create_task"

# Show test names (don't run)
pytest --collect-only tests/test_activities.py

# Run with verbose output
pytest -vv tests/

# Run with output capture disabled (see print statements)
pytest -s tests/

# Run with coverage
pytest --cov=src tests/
coverage report

# Run specific test with debugging
pytest -vv --pdb tests/test_activities.py::TestActivitiesRoutes::test_create_task
```

### Expected Test Results

```
tests/test_activities.py::TestActivitiesRoutes::test_create_task PASSED
tests/test_activities.py::TestActivitiesRoutes::test_get_task PASSED
tests/test_activities.py::TestActivitiesRoutes::test_list_tasks PASSED
tests/test_activities.py::TestActivitiesRoutes::test_create_task_validation PASSED
tests/test_activities.py::TestActivitiesRoutes::test_get_nonexistent_task PASSED

====== 5 passed in 0.25s ======
```

---

## 11. Test Organization

### File Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_activities.py       # Activities routes & service tests
├── test_alerts.py           # Alerts module tests
├── test_programmes.py       # Programmes module tests
├── test_staff.py            # Staff module tests
├── test_reports.py          # Reports module tests
├── test_event_bus.py        # EventBus tests
└── test_errors.py           # Error handling tests
```

### Test Class Organization

```python
class TestActivitiesRoutes:
    """Tests for activities HTTP routes."""
    
    # Route tests organized by operation
    def test_create_task(self, client: TestClient) -> None:
        pass
    
    def test_get_task(self, client: TestClient) -> None:
        pass
    
    def test_list_tasks(self, client: TestClient) -> None:
        pass
    
    def test_create_task_validation(self, client: TestClient) -> None:
        pass


class TestActivitiesService:
    """Tests for activities service logic."""
    
    @pytest.mark.asyncio
    async def test_create_task_validation(self) -> None:
        pass
```

---

## 12. Checklist for New Features

Before submitting a PR, verify all tests pass:

- [ ] All routes have tests (happy path + error paths)
- [ ] All validation is tested
- [ ] Error responses are tested (422, 404, 409, 400)
- [ ] Events are tested for correctness
- [ ] Integration between modules tested
- [ ] Pagination tested
- [ ] Filtering tested
- [ ] Each acceptance criterion has a test
- [ ] `pytest` passes without errors
- [ ] `mypy src` passes
- [ ] `ruff check src` passes
- [ ] Code coverage > 80%

### Verification Commands

```bash
# Run everything required before commit
pytest && mypy src && ruff check src

# Or individually
pytest                          # Tests
mypy src                       # Type checking
ruff check src                 # Linting
pytest --cov=src tests/        # Coverage
```

---

## Quick Reference: HTTP Status Codes

| Status | Scenario | Example |
|--------|----------|---------|
| 200 | GET success | `GET /tasks/{id}` |
| 201 | Created | `POST /tasks` |
| 204 | Deleted | `DELETE /tasks/{id}` |
| 400 | Business rule violation | Can't reopen completed task |
| 404 | Resource not found | `GET /tasks/nonexistent` |
| 409 | Conflict/duplicate | Duplicate email in staff |
| 422 | Validation error | Empty title |

---

## Examples from Repository

### Real Example: Activities Tests

**File:** `tests/test_activities.py`

```python
class TestActivitiesRoutes:
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

    def test_get_nonexistent_task(self, client: TestClient) -> None:
        """Test getting non-existent task."""
        response = client.get("/api/v1/activities/tasks/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "NOT_FOUND"
```

---

*For coding conventions, see [[coding-conventions]]. For component patterns, see [[component-patterns]]. For architectural principles, see [[architecture-principles]].*
