# StoreOps Repository Architecture Assessment

**Version:** 0.1.0  
**Assessment Date:** 2026-08-29  
**Platform:** Python 3.12+ FastAPI Application

---

## Table of Contents

1. [Module Structure](#module-structure)
2. [Route → Service → Repository Architecture](#route--service--repository-architecture)
3. [EventBus Implementation](#eventbus-implementation)
4. [Error Handling Strategy](#error-handling-strategy)
5. [Testing Conventions](#testing-conventions)
6. [Dependency Boundaries](#dependency-boundaries)
7. [Coding Standards](#coding-standards)
8. [Harness Skill Mapping](#harness-skill-mapping)

---

## Module Structure

### Overview

StoreOps is organized as a **modular monolith** with domain-driven structure. Each domain is self-contained with clear separation of concerns.

### Module Organization

```
src/
├── activities/          # Task/activity management
│   ├── models.py        # Pydantic schemas (TaskBase, Task, TaskCreate, TaskUpdate, TaskList)
│   ├── routes.py        # HTTP endpoints (POST, GET, PUT, DELETE)
│   ├── service.py       # Business logic (ActivitiesService)
│   ├── repository.py    # Data access (ActivitiesRepository)
│   └── __init__.py
├── alerts/              # Alert & escalation management
│   ├── models.py        # Alert domain models
│   ├── routes.py        # Alert endpoints
│   ├── service.py       # Alert business logic
│   ├── repository.py    # Alert persistence
│   └── __init__.py
├── programmes/          # Programme/initiative management
│   ├── models.py
│   ├── routes.py
│   ├── service.py
│   ├── repository.py
│   └── __init__.py
├── reports/             # Reporting & analytics
│   ├── models.py
│   ├── routes.py
│   ├── service.py
│   ├── repository.py
│   └── __init__.py
├── staff/               # Staff management
│   ├── models.py
│   ├── routes.py
│   ├── service.py
│   ├── repository.py
│   └── __init__.py
├── shared/              # Cross-cutting concerns
│   ├── errors.py        # Error hierarchy (AppError, ValidationError, NotFoundError, BusinessRuleViolationError, ConflictError)
│   ├── event_bus.py     # In-memory event bus (EventBus, EventType, get_event_bus)
│   ├── dependencies.py  # FastAPI dependency injection (get_event_bus_dependency, get_db_session)
│   └── __init__.py
└── main.py              # Application factory & router registration

tests/
├── conftest.py          # Pytest configuration, shared fixtures
├── test_activities.py
├── test_alerts.py
├── test_errors.py
├── test_event_bus.py
├── test_programmes.py
├── test_reports.py
├── test_staff.py
└── __init__.py
```

### Modules at a Glance

| Module | Purpose | Key Models | Key Operations |
|--------|---------|------------|-----------------|
| **activities** | Task lifecycle management | Task, TaskStatus, TaskPriority, TaskCategory | CRUD, list by status, list by user |
| **alerts** | Alert triggering & escalation | Alert, AlertStatus, AlertSeverity | CRUD, filter by status/severity |
| **programmes** | Programme/initiative tracking | Programme, ProgrammeStatus | CRUD, lifecycle transitions |
| **reports** | Analytics & reporting | Report, ReportType | Generate, retrieve, export |
| **staff** | Staff/user management | Staff, StaffRole | CRUD, list by store, list by role |
| **shared** | Cross-module utilities | AppError, EventBus, ErrorCode | Error handling, event publishing |

---

## Route → Service → Repository Architecture

### Architectural Pattern: Layered Hexagonal Architecture

StoreOps implements a **strict three-layer architecture** with unidirectional dependencies:

```
HTTP Layer (Routes)
      ↓ (calls)
Business Logic Layer (Services)
      ↓ (calls)
Data Access Layer (Repositories)
```

### Layer Responsibilities

#### 1. **Routes Layer** (`routes.py`)

**File:** `src/{module}/routes.py`

**Responsibilities:**
- HTTP request/response handling only
- Request validation via Pydantic models
- Exception handling & HTTP status mapping
- No business logic
- No repository access (always via Service)
- Format JSON responses

**Pattern Example:**
```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task_create: TaskCreate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    try:
        return await service.create_task(task_create=task_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

**Key Characteristics:**
- Uses FastAPI's `APIRouter` with consistent prefix: `/api/v1/{module}`
- Dependency injection via `Depends()` for service instances
- All business exceptions converted to `HTTPException`
- Response models are Pydantic schemas (never raw dicts)
- No QueryParams without validation constraints

---

#### 2. **Service Layer** (`service.py`)

**File:** `src/{module}/service.py`

**Responsibilities:**
- All business logic & domain rules
- Input validation (beyond Pydantic)
- Orchestration across repositories
- Event publishing
- Always raise `AppError` or subclasses
- Can read from other modules' services (unidirectional dependency)
- Database transaction boundaries
- Cross-module side effects

**Pattern Example:**
```python
class ActivitiesService:
    def __init__(self, repository: ActivitiesRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus

    async def create_task(self, task_create: TaskCreate) -> Task:
        # Validation
        if not task_create.title or not task_create.title.strip():
            raise ValidationError(message="Task title is required")
        
        # Persist
        task = await self.repository.create(task_create)
        
        # Publish event for other modules
        await self.event_bus.publish(EventType.TASK_CREATED, {...})
        return task
```

**Key Characteristics:**
- Constructor accepts repository & event_bus (dependency injection)
- All methods are async
- Raises only `AppError` subclasses
- Queries repositories only (no direct data access)
- Publishes domain events
- Business rule violations raise `BusinessRuleViolationError`

**Factory Pattern:**
```python
async def get_activities_service() -> ActivitiesService:
    """FastAPI dependency factory."""
    repository = get_activities_repository()
    event_bus = get_event_bus()
    return ActivitiesService(repository=repository, event_bus=event_bus)
```

---

#### 3. **Repository Layer** (`repository.py`)

**File:** `src/{module}/repository.py`

**Responsibilities:**
- Direct data access only
- No business logic
- No external service calls
- No service imports (circular dependency prevention)
- CRUD operations
- Pagination
- Filtering

**Pattern Example:**
```python
class ActivitiesRepository:
    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, task_create: TaskCreate, created_by: str | None = None) -> Task:
        """Create new task."""
        self._counter += 1
        task_id = f"task_{self._counter}"
        task_data = {...}
        self._tasks[task_id] = task_data
        return Task.model_validate(task_data)

    async def get_by_id(self, task_id: str) -> Task | None:
        """Get by ID."""
        task_data = self._tasks.get(task_id)
        return Task.model_validate(task_data) if task_data else None

    async def list_all(self, skip: int = 0, limit: int = 10) -> tuple[list[Task], int]:
        """List with pagination."""
        all_tasks = list(self._tasks.values())
        total = len(all_tasks)
        tasks = all_tasks[skip : skip + limit]
        return [Task.model_validate(t) for t in tasks], total
```

**Key Characteristics:**
- Maintains in-memory storage (future: replace with SQLAlchemy ORM)
- All methods are async
- Returns domain models, not raw data dicts
- Implements pagination pattern: `list_*()` returns `tuple[list[Model], int]`
- `reset()` method for testing
- Single global instance (singleton via `get_*_repository()`)

**Factory Pattern:**
```python
_repository: ActivitiesRepository | None = None

def get_activities_repository() -> ActivitiesRepository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = ActivitiesRepository()
    return _repository
```

### Call Flow Example

**Request:** `POST /api/v1/activities/tasks`

1. **Routes** receives `task_create: TaskCreate`
2. **Routes** calls `service.create_task(task_create)`
3. **Service** validates business rules
4. **Service** calls `repository.create(task_create, created_by)`
5. **Repository** creates task, returns `Task` model
6. **Service** publishes `TASK_CREATED` event
7. **Service** returns `Task` to **Routes**
8. **Routes** formats as JSON 201 response

---

## EventBus Implementation

### Purpose

**Cross-module communication without direct coupling.** Modules publish domain events; other modules subscribe and react.

### Design Pattern: Publish-Subscribe (In-Memory)

**File:** `src/shared/event_bus.py`

### Key Components

#### **EventType Enum**

```python
class EventType(StrEnum):
    # Activities events
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_OVERDUE = "TASK_OVERDUE"
    TASK_ASSIGNED = "TASK_ASSIGNED"

    # Programmes events
    PROGRAMME_CREATED = "PROGRAMME_CREATED"
    PROGRAMME_STARTED = "PROGRAMME_STARTED"
    PROGRAMME_COMPLETED = "PROGRAMME_COMPLETED"

    # Staff events
    STAFF_ONBOARDED = "STAFF_ONBOARDED"
    STAFF_OFFBOARDED = "STAFF_OFFBOARDED"

    # Alerts events
    SLA_BREACH = "SLA_BREACH"
    CRITICAL_ALERT = "CRITICAL_ALERT"
    ESCALATION_NEEDED = "ESCALATION_NEEDED"

    # Reports events
    REPORT_GENERATED = "REPORT_GENERATED"
```

#### **EventBus Class**

```python
class EventBus:
    """Lightweight in-memory event bus."""
    
    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}
        self._event_history: list[tuple[str, dict[str, Any]]] = []

    async def publish(
        self,
        event_type: EventType | str,
        payload: dict[str, Any],
    ) -> None:
        """Publish event to all subscribers."""
        event_key = str(event_type)
        self._event_history.append((event_key, payload))
        
        if event_key not in self._handlers:
            return
        
        for handler in self._handlers[event_key]:
            await handler(payload)

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """Subscribe to event type. Returns unsubscribe function."""
        event_key = str(event_type)
        if event_key not in self._handlers:
            self._handlers[event_key] = []
        
        self._handlers[event_key].append(handler)
        
        def unsubscribe() -> None:
            self._handlers[event_key].remove(handler)
        return unsubscribe

    def get_event_history(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all published events (testing/debugging)."""
        return self._event_history.copy()

    def reset(self) -> None:
        """Reset event bus (clear handlers and history)."""
        self._handlers.clear()
        self._event_history.clear()
```

### Usage Pattern

**Publishing:**
```python
# In ActivitiesService
await self.event_bus.publish(
    EventType.TASK_CREATED,
    {
        "task_id": task.id,
        "title": task.title,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
    },
)
```

**Subscribing:**
```python
# In AlertsService or app startup
async def handle_task_created(payload: dict) -> None:
    # React to task creation
    task_id = payload["task_id"]
    # Trigger alert logic

event_bus.subscribe(EventType.TASK_CREATED, handle_task_created)
```

### Key Properties

- **Synchronous event delivery:** All handlers execute sequentially (currently; can be parallelized)
- **In-memory only:** Events lost on restart (future: persist to message queue)
- **Global singleton:** Single EventBus instance across all modules
- **Event history:** Tracks all events for testing/auditing
- **Testable:** History can be inspected in unit tests
- **No guaranteed delivery:** If a handler fails, subsequent handlers may not execute (future: add error handling)

### Dependency Injection

```python
# In routes
async def create_task(
    service: ActivitiesService = Depends(get_activities_service),
):
    # get_activities_service returns service with event_bus already injected
    
# In service factory
async def get_activities_service() -> ActivitiesService:
    repository = get_activities_repository()
    event_bus = get_event_bus()  # Singleton
    return ActivitiesService(repository=repository, event_bus=event_bus)
```

---

## Error Handling Strategy

### Error Hierarchy

All errors in services are instances of `AppError` or its subclasses. Raw exceptions are never raised.

**File:** `src/shared/errors.py`

### Error Types

#### 1. **AppError** (Base)

```python
class AppError(Exception):
    def __init__(
        self,
        error_code: ErrorCode | str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }
```

#### 2. **ValidationError**

**Raised when:** Input validation fails  
**HTTP Status:** 422 Unprocessable Entity

```python
if not task_create.title or not task_create.title.strip():
    raise ValidationError(message="Task title is required")
```

#### 3. **NotFoundError**

**Raised when:** Resource doesn't exist  
**HTTP Status:** 404 Not Found

```python
task = await self.repository.get_by_id(task_id)
if not task:
    raise NotFoundError(resource_type="Task", resource_id=task_id)
```

**JSON Response:**
```json
{
    "error_code": "NOT_FOUND",
    "message": "Task with ID 123 not found",
    "details": {"resource_type": "Task", "resource_id": "123"}
}
```

#### 4. **BusinessRuleViolationError**

**Raised when:** Domain rule violated  
**HTTP Status:** 400 Bad Request

```python
if task.status == TaskStatus.DONE and not task.completed_date:
    raise BusinessRuleViolationError(
        message="Cannot mark task as done without completion date",
        rule_name="TASK_COMPLETION_REQUIRES_DATE"
    )
```

#### 5. **ConflictError**

**Raised when:** Resource already exists (duplicate)  
**HTTP Status:** 409 Conflict

```python
existing = await self.repository.get_by_email(staff_create.email)
if existing:
    raise ConflictError(
        resource_type="Staff",
        message=f"Staff member with email {staff_create.email} already exists",
    )
```

#### 6. **ErrorCode Enum**

```python
class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    CONFLICT = "CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
```

### Error Handling in Routes

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task_create: TaskCreate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    try:
        return await service.create_task(task_create=task_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Error Handling in main.py

```python
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    """Handle AppError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
```

### Principles

1. ✅ **Never raise raw exceptions** (ValueError, RuntimeError, etc.)
2. ✅ **Always use AppError subclasses** in services
3. ✅ **Preserve error context** in details dict
4. ✅ **Consistent JSON error format** across all endpoints
5. ✅ **Testable error handling** with specific error codes

---

## Testing Conventions

### Testing Framework

**Framework:** Pytest with pytest-asyncio  
**Client:** FastAPI TestClient (synchronous wrapper)  
**Location:** `tests/` directory

### Test Structure

#### conftest.py - Shared Fixtures

```python
@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset all repositories and event bus before/after each test."""
    reset_event_bus()
    get_activities_repository().reset()
    get_programmes_repository().reset()
    get_staff_repository().reset()
    get_alerts_repository().reset()
    get_reports_repository().reset()
    yield
    # Cleanup after test
    reset_event_bus()
    # ... reset all repos again
```

#### Test Organization

```python
# test_activities.py

class TestActivitiesRoutes:
    """Tests for activities HTTP routes."""

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
        # Setup: Create task
        task_data = {...}
        create_response = client.post("/api/v1/activities/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Execute
        response = client.get(f"/api/v1/activities/tasks/{task_id}")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id

    def test_list_tasks(self, client: TestClient) -> None:
        """Test listing tasks."""
        # Setup: Create multiple tasks
        for i in range(3):
            task_data = {
                "title": f"Task {i}",
                "priority": TaskPriority.LOW,
                "category": TaskCategory.RESTOCKING,
            }
            client.post("/api/v1/activities/tasks", json=task_data)

        # Execute
        response = client.get("/api/v1/activities/tasks")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
```

#### Async Test Pattern

```python
# test_event_bus.py

@pytest.fixture
def event_bus() -> EventBus:
    """Create event bus instance."""
    reset_event_bus()
    from src.shared.event_bus import get_event_bus
    return get_event_bus()

class TestEventBus:
    """Tests for event bus."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus: EventBus) -> None:
        """Test publishing and subscribing to events."""
        received_events = []

        async def handler(payload: dict) -> None:
            received_events.append(payload)

        # Subscribe
        event_bus.subscribe(EventType.TASK_CREATED, handler)

        # Publish
        await event_bus.publish(
            EventType.TASK_CREATED,
            {"task_id": "123", "title": "Test Task"},
        )

        # Verify
        assert len(received_events) == 1
        assert received_events[0]["task_id"] == "123"
```

### Testing Conventions

1. ✅ **Class-based organization:** `TestModule`, `TestService`, etc.
2. ✅ **Fixture isolation:** `reset_state` fixture (autouse) prevents test pollution
3. ✅ **Async tests:** `@pytest.mark.asyncio` for async functions
4. ✅ **Naming:** `test_*` for functions, `Test*` for classes
5. ✅ **Setup/Execute/Verify:** AAA pattern (Arrange, Act, Assert)
6. ✅ **Integration tests:** Use `TestClient` to test full route → service → repository flow
7. ✅ **Event verification:** Check `event_bus.get_event_history()` in integration tests
8. ✅ **Error testing:** Test both success and error paths

### pytest.ini Configuration

```ini
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
asyncio_mode = "auto"
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

---

## Dependency Boundaries

### Dependency Graph

```
routes.py
  ├─ depends on → service.py
  ├─ depends on → models.py (Pydantic)
  └─ depends on → errors.py

service.py
  ├─ depends on → repository.py
  ├─ depends on → event_bus.py
  ├─ depends on → models.py
  ├─ depends on → errors.py
  └─ MAY depend on → other modules' service.py (READ-ONLY)

repository.py
  ├─ depends on → models.py
  └─ ⚠️ MUST NOT depend on → service.py (circular dependency prevention)

models.py
  └─ depends on → pydantic (only external dependency)

errors.py
  └─ NO internal dependencies

event_bus.py
  └─ NO internal dependencies

dependencies.py
  └─ depends on → event_bus.py
```

### Allowed Dependencies

✅ **Routes can call Services**  
✅ **Services can call Repositories**  
✅ **Services can call other Services** (for read-only queries)  
✅ **Services can publish Events**  
✅ **Routes can catch AppError**  
✅ **All layers can raise AppError subclasses**  

### Forbidden Dependencies

❌ **Routes cannot call Repositories directly**  
❌ **Repositories cannot import Services**  
❌ **Repositories cannot publish Events**  
❌ **Circular imports** (e.g., module A service depends on module B service which depends on module A service)

### Module-to-Module Communication

**Pattern:** Publish-Subscribe via EventBus

```
Activities Service publishes TASK_CREATED event
                    ↓
            EventBus (global singleton)
                    ↓
Alerts Service subscribes to TASK_CREATED
Alerts Service reacts without knowing about Activities
```

**Never direct coupling:**
```python
# ❌ BAD: Direct service call
class AlertsService:
    def __init__(self, activities_service: ActivitiesService):
        self.activities_service = activities_service  # Forbidden!

# ✅ GOOD: Event-based
class AlertsService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.TASK_CREATED, self.handle_task_created)

    async def handle_task_created(self, payload: dict) -> None:
        # React to task creation
        pass
```

---

## Coding Standards

### Code Style & Linting

**Tool:** Ruff (fast Python linter)  
**Config:** `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "PIE", "PT", "RUF"]
ignore = ["E501", "B008", "B904"]
```

#### Selected Rules

- **E/W:** PEP 8 errors and warnings
- **F:** Pyflakes (logical errors)
- **I:** Isort (import sorting)
- **N:** PEP 8 naming conventions
- **UP:** Modernize Python syntax
- **B:** Bugbear (security & best practices)
- **A:** Shadowing of builtins
- **C4:** Code complexity
- **PIE:** Pie (performance)
- **PT:** Pytest best practices
- **RUF:** Ruff-specific rules

### Type Checking

**Tool:** Mypy  
**Config:** `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

**Strict mode:** All functions must have type hints.

### Python Version & Dependencies

**Minimum:** Python 3.12+

**Core Dependencies:**
```
fastapi==0.104.1        # Web framework
uvicorn[standard]==0.24.0 # ASGI server
pydantic==2.5.0         # Data validation
sqlalchemy==2.0.23      # ORM (future use)
psycopg2-binary==2.9.9  # PostgreSQL driver (future use)
alembic==1.13.0         # Migrations (future use)
```

**Dev Dependencies:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
ruff==0.1.8
mypy==1.7.1
```

### Naming Conventions

#### Modules
```python
# lowercase_with_underscores
activities/
    models.py
    routes.py
    service.py
    repository.py
```

#### Classes
```python
# PascalCase
class ActivitiesService:
    pass

class TaskRepository:
    pass

class NotFoundError(AppError):
    pass

class EventBus:
    pass
```

#### Functions/Methods
```python
# lowercase_with_underscores
async def get_task(task_id: str) -> Task:
    pass

async def list_tasks(skip: int = 0, limit: int = 10) -> tuple[list[Task], int]:
    pass

def reset(self) -> None:
    pass
```

#### Constants
```python
# UPPERCASE_WITH_UNDERSCORES
MAX_PAGE_SIZE = 100
DEFAULT_SKIP = 0
DEFAULT_LIMIT = 10
```

#### Private/Protected
```python
# Prefix with _
_event_bus: EventBus | None = None
self._handlers: dict[str, list[EventHandler]] = {}
self._tasks: dict[str, dict[str, Any]] = {}
```

### Code Organization Within Files

#### models.py
```python
"""Data models for {Module} module."""

from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field

# 1. Enums first
class TaskStatus(StrEnum):
    pass

# 2. Base models
class TaskBase(BaseModel):
    pass

# 3. Request models
class TaskCreate(TaskBase):
    pass

# 4. Response models
class Task(TaskBase):
    pass

# 5. List/pagination models
class TaskList(BaseModel):
    pass
```

#### service.py
```python
"""Service layer for {Module} module.

Responsibilities:
- Business logic
- Validation
- Orchestration
- Publishing events
- Always raise AppError (never raw exceptions)
- Call repositories only
- May read from other modules' services
"""

from src.{module}.models import ...
from src.{module}.repository import ...
from src.shared.errors import ...
from src.shared.event_bus import ...

class MyService:
    def __init__(self, repository: MyRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus

    async def create(self, ...):
        # Validation
        # Persist via repository
        # Publish event
        # Return

    async def get(self, id: str):
        pass

    # ... more methods

async def get_my_service() -> MyService:
    repository = get_my_repository()
    event_bus = get_event_bus()
    return MyService(repository=repository, event_bus=event_bus)
```

#### repository.py
```python
"""Repository layer for {Module} module.

Responsibilities:
- Direct data access
- No business logic
- No external service calls
- No service imports (circular dependency prevention)
"""

from datetime import UTC, datetime
from typing import Any
from src.{module}.models import ...

class MyRepository:
    def __init__(self):
        self._data: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, ...):
        pass

    async def get_by_id(self, id: str):
        pass

    async def list_all(self, skip: int = 0, limit: int = 10):
        pass

    async def update(self, id: str, ...):
        pass

    async def delete(self, id: str):
        pass

    def reset(self) -> None:
        self._data.clear()
        self._counter = 0

_repository: MyRepository | None = None

def get_my_repository() -> MyRepository:
    global _repository
    if _repository is None:
        _repository = MyRepository()
    return _repository
```

#### routes.py
```python
"""Route handlers for {Module} module.

Responsibilities:
- HTTP request/response handling
- No business logic
- Call services only
- Format responses
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from src.{module}.models import ...
from src.{module}.service import ...
from src.shared.errors import AppError

router = APIRouter(
    prefix="/api/v1/{module}",
    tags=["{module}"],
)

@router.post("/resource", response_model=Model, status_code=201)
async def create_resource(
    resource_data: ModelCreate,
    service: MyService = Depends(get_my_service),
) -> Model:
    try:
        return await service.create(...)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

@router.get("/resource/{id}", response_model=Model)
async def get_resource(
    id: str,
    service: MyService = Depends(get_my_service),
) -> Model:
    try:
        return await service.get(id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

@router.get("/resource", response_model=ListModel)
async def list_resources(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: MyService = Depends(get_my_service),
) -> ListModel:
    result = await service.list(skip=skip, limit=limit)
    return ListModel(**result)
```

### Code Quality Principles

1. ✅ **Type hints everywhere:** `disallow_untyped_defs = true`
2. ✅ **Async/await:** All I/O is async (awaitable functions)
3. ✅ **Docstrings:** All public functions/classes have module docstrings
4. ✅ **100 character line limit:** (Ruff enforced)
5. ✅ **DRY principle:** No duplication across layers
6. ✅ **SOLID principles:** Especially Single Responsibility & Dependency Inversion
7. ✅ **No magic numbers:** Use constants
8. ✅ **Explicit is better than implicit:** Clear intent, readable code
9. ✅ **Fail fast:** Validate early, raise AppError early
10. ✅ **Comments for WHY, not WHAT:** Code should be self-documenting

---

## Harness Skill Mapping

### Overview

The StoreOps codebase architecture maps naturally to a set of **Claude Code harness skills**. These skills encapsulate domain knowledge, patterns, and conventions that accelerate development.

### Recommended Skill Files

The following skill files should be created to codify StoreOps patterns and accelerate future development:

#### 1. **app-context.md**

**Purpose:** Provide Claude with essential repository context for any task.

**Content:**
- Repository purpose (Retail Operations Management REST API)
- Tech stack (FastAPI, Python 3.12, Pydantic)
- Module list with brief descriptions
- Architectural overview (Route → Service → Repository)
- Development environment setup

**Trigger:** Should be loaded on every session start to establish common ground.

**Example Hook:**
```json
{
  "name": "app-context-on-session-start",
  "trigger": "session_start",
  "action": "skill",
  "args": {"skill": "app-context"}
}
```

---

#### 2. **architecture-principles.md**

**Purpose:** Encode architectural patterns, constraints, and decision rationale.

**Content:**
- Layered hexagonal architecture (Routes → Services → Repositories)
- EventBus publish-subscribe pattern
- Dependency boundaries (what can call what)
- Module-to-module communication strategy
- Testing architecture
- Error handling philosophy

**Usage:** Reference when designing new features or modules.

**Example Sections:**
```markdown
## Core Principles

### 1. Three-Layer Architecture
- Routes: HTTP handling only
- Services: Business logic & orchestration
- Repositories: Data access only

### 2. Dependency Direction
- Routes → Services → Repositories (unidirectional)
- Never: Repositories → Services
- Never: Circular imports

### 3. Cross-Module Communication
- Use EventBus, not direct service calls
- Modules are loosely coupled via events
- Activities doesn't know about Alerts

### 4. Error Handling
- All services raise AppError or subclasses
- Never raw exceptions
- Routes catch AppError and convert to HTTPException
```

---

#### 3. **coding-conventions.md**

**Purpose:** Document code style, naming, file organization, and quality standards.

**Content:**
- Python version (3.12+)
- Linting rules (Ruff configuration)
- Type checking (Mypy strict mode)
- Naming conventions (classes, functions, constants)
- File organization patterns
- Import ordering
- Docstring format
- Line length (100 chars)
- Code organization within models.py, service.py, repository.py, routes.py

**Usage:** Reference when writing new code or reviewing pull requests.

**Example:**
```markdown
## Naming Conventions

### Classes
- PascalCase: `ActivitiesService`, `NotFoundError`, `EventBus`

### Functions/Methods
- lowercase_with_underscores: `get_task()`, `list_tasks()`, `reset()`

### Constants
- UPPERCASE_WITH_UNDERSCORES: `MAX_PAGE_SIZE = 100`

### Private/Protected
- Prefix with underscore: `_event_bus`, `_handlers`, `_tasks`

## File Organization

### models.py
1. Enums (TaskStatus, TaskPriority, etc.)
2. Base models
3. Request models (Create, Update)
4. Response models
5. List/pagination models

### service.py
1. Service class with __init__, then public methods
2. Factory function at end: get_*_service()

### repository.py
1. Repository class with CRUD methods
2. reset() method for testing
3. Global singleton instance
4. Factory function at end: get_*_repository()

### routes.py
1. Router configuration with prefix and tags
2. HTTP endpoints in logical order (POST, GET, PUT, DELETE)
3. Consistent error handling pattern
```

---

#### 4. **how-to-test.md**

**Purpose:** Document testing conventions and patterns.

**Content:**
- Testing framework (Pytest + pytest-asyncio)
- TestClient usage
- Fixture patterns (reset_state, event_bus)
- Test organization (class-based)
- AAA pattern (Arrange, Act, Assert)
- Integration test patterns
- Event bus verification in tests
- Error path testing
- Async test syntax

**Usage:** Reference when writing new tests.

**Example:**
```markdown
## Test Structure

### conftest.py Fixture Pattern
```python
@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset all state before/after each test."""
    reset_event_bus()
    get_activities_repository().reset()
    # Reset all other repos
    yield
    # Cleanup (same as setup)
```

### Integration Test Pattern
```python
class TestActivitiesRoutes:
    def test_create_task(self, client: TestClient) -> None:
        # Arrange
        task_data = {...}
        
        # Act
        response = client.post("/api/v1/activities/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["title"] == "Test Task"

### Event Verification in Tests
```python
def test_task_creation_publishes_event(self, client: TestClient) -> None:
    # Create task
    client.post("/api/v1/activities/tasks", json={...})
    
    # Verify event was published
    from src.shared.event_bus import get_event_bus
    event_bus = get_event_bus()
    history = event_bus.get_event_history()
    assert len(history) > 0
    assert history[0][0] == EventType.TASK_CREATED
```
```

---

#### 5. **how-to-review.md**

**Purpose:** Encode code review criteria and patterns for this codebase.

**Content:**
- Architectural review checklist (dependency boundaries, layers)
- Type safety verification (Mypy compliance)
- Test coverage expectations
- Error handling review (using AppError?)
- Event-based communication review
- Database query optimization (when using SQLAlchemy)
- Performance considerations
- Security considerations
- Common pitfalls to watch for

**Usage:** Reference when reviewing pull requests or when using `/code-review` skill.

**Example:**
```markdown
## Architecture Review Checklist

- [ ] Routes only handle HTTP, no business logic
- [ ] Services contain all business logic
- [ ] Repositories handle only data access
- [ ] No direct repository imports in routes
- [ ] No service imports in repositories
- [ ] All errors are AppError subclasses
- [ ] EventBus used for cross-module communication
- [ ] No direct service-to-service dependencies
- [ ] Dependency injection via constructors
- [ ] All functions have type hints
- [ ] Tests use reset_state fixture
- [ ] Integration tests verify events

## Common Pitfalls

### ❌ Direct repository call in route
Routes should not call repositories directly.

### ❌ Missing type hints
All functions must have type hints (Mypy disallow_untyped_defs).

### ❌ Circular imports
Services must not import other services unless read-only.

### ❌ Raw exceptions in service
Always raise AppError subclasses.
```

---

#### 6. **evaluation-rules.md**

**Purpose:** Define success criteria and evaluation metrics for features and PRs.

**Content:**
- Architectural compliance (follows Route → Service → Repository)
- Test coverage expectations (minimum %)
- Performance baselines
- Security requirements
- Documentation requirements
- Code quality metrics (Mypy, Ruff)

**Usage:** Reference when evaluating pull requests or features.

**Example:**
```markdown
## Evaluation Criteria

### Architectural Compliance (Required)
- [ ] Route handlers only perform HTTP handling
- [ ] Business logic isolated in services
- [ ] Data access isolated in repositories
- [ ] No dependency rule violations
- [ ] Cross-module communication via events
- [ ] Error handling follows AppError pattern

### Test Coverage (Required)
- [ ] Minimum 80% code coverage
- [ ] Integration tests for routes
- [ ] Service logic tests
- [ ] Error path tests
- [ ] Event publishing verified

### Code Quality (Required)
- [ ] Ruff passes (no linting errors)
- [ ] Mypy passes (strict mode)
- [ ] 100 char line length enforced
- [ ] Type hints on all functions
- [ ] Docstrings on public functions

### Documentation (Required)
- [ ] Docstrings in code
- [ ] README updated if adding new module
- [ ] API changes documented
```

---

### Skill Manifest Summary

| Skill | Purpose | Audience | Trigger |
|-------|---------|----------|---------|
| **app-context** | Essential repo context | All | Session start |
| **architecture-principles** | Architectural decisions | Designers | Feature design |
| **coding-conventions** | Code style & standards | Developers | Code writing |
| **how-to-test** | Testing patterns | QA/Developers | Test writing |
| **how-to-review** | Code review criteria | Reviewers | PR review |
| **evaluation-rules** | Success criteria | Evaluators | Acceptance |

### Usage Workflow

1. **Session Start:** Load `app-context` to establish common ground
2. **Feature Design:** Load `architecture-principles` when designing new modules
3. **Code Writing:** Load `coding-conventions` for style guidance
4. **Test Writing:** Load `how-to-test` for patterns
5. **Code Review:** Load `how-to-review` for review checklist
6. **Acceptance:** Load `evaluation-rules` for evaluation metrics

---

## Quick Reference

### File Paths by Concern

| Concern | File | Pattern |
|---------|------|---------|
| Error hierarchy | `src/shared/errors.py` | AppError + subclasses |
| Event definitions | `src/shared/event_bus.py` | EventType enum |
| HTTP routes | `src/{module}/routes.py` | APIRouter + handlers |
| Business logic | `src/{module}/service.py` | Service class + factory |
| Data access | `src/{module}/repository.py` | Repository + singleton |
| Data models | `src/{module}/models.py` | Pydantic BaseModel |
| Testing | `tests/conftest.py` | Fixtures + reset_state |

### Common Commands

```bash
# Run tests
pytest

# Run type check
mypy src

# Run linter
ruff check src

# Format code
ruff format src

# Run server
python -m src.main

# List available routes
curl http://localhost:8000/api/v1
```

---

## Next Steps for Harness Integration

1. ✅ Create `docs/architecture-principles.md` from this document
2. ✅ Create `docs/coding-conventions.md` from code standards section
3. ✅ Create `docs/how-to-test.md` from testing conventions section
4. ✅ Create `docs/how-to-review.md` from review criteria
5. ✅ Create `docs/evaluation-rules.md` from success criteria
6. ✅ Create `docs/app-context.md` from module overview
7. 🔄 Register skills in harness configuration
8. 🔄 Set up hooks for automatic skill loading
9. 🔄 Create PR template referencing evaluation rules
10. 🔄 Create contribution guidelines referencing all skills

---

## Document Metadata

**Author:** Claude Code - Architecture Analysis  
**Created:** 2026-08-29  
**Version:** 1.0.0  
**Status:** Complete Assessment  
**Source:** Full codebase analysis  
**Scope:** StoreOps API v0.1.0 Python 3.12+ FastAPI  

---

*This assessment document serves as the authoritative reference for StoreOps architecture, conventions, and harness skill mappings. Update as the codebase evolves.*
