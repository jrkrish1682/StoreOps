# StoreOps Application Context

**Version:** 0.1.0  
**Last Updated:** 2026-08-29  
**Platform:** Python 3.12+ FastAPI Application

---

## Purpose

This skill provides Claude Code agents with the minimum knowledge required to understand, navigate, and contribute to the StoreOps REST API application.

**Use this skill when:**
- Starting any new task in this repository
- Onboarding new contributors
- Establishing common ground for multi-step workflows
- Understanding architectural decisions

---

## 1. Business Domain Overview

### What is StoreOps?

**StoreOps** is a **Retail Operations Management REST API** built with FastAPI. It manages five core business domains:

- **Activities (Tasks):** Task/activity lifecycle management for store operations
- **Programmes:** Initiative and programme tracking across stores or regions
- **Staff:** Staff/user management with role-based organization
- **Alerts:** Alert triggering and escalation management
- **Reports:** Analytics and reporting engine for operational insights

### Key Context

- **Target Users:** Store managers, regional supervisors, analytics teams
- **Deployment:** Cloud-ready ASGI application (Uvicorn)
- **Data Storage:** Currently in-memory; future: PostgreSQL via SQLAlchemy ORM
- **API Versioning:** `/api/v1/*` endpoints

---

## 2. Module Ownership & Responsibilities

Each module is self-contained with its own models, routes, service, and repository layers.

### Activities Module
**Purpose:** Task and activity lifecycle management  
**Location:** `src/activities/`

**Key Models:**
- `Task` - Core task entity with status, priority, category
- `TaskStatus` - Enum: TODO, IN_PROGRESS, DONE, BLOCKED
- `TaskPriority` - Enum: LOW, MEDIUM, HIGH, CRITICAL
- `TaskCategory` - Enum: OPERATIONAL, COMPLIANCE, RESTOCKING, PLANOGRAM, MAINTENANCE

**Operations:**
- Create tasks with validation
- Retrieve tasks by ID
- List all tasks with pagination
- Update task status/properties
- Delete tasks
- Filter tasks by status or assigned user

**Events Published:**
- `TASK_CREATED` - When a new task is created
- `TASK_COMPLETED` - When task status changes to DONE
- `TASK_ASSIGNED` - When task is assigned to user
- `TASK_OVERDUE` - When task exceeds due date

### Programmes Module
**Purpose:** Initiative/programme tracking and lifecycle management  
**Location:** `src/programmes/`

**Key Models:**
- `Programme` - Programme entity with status, scope, timeline
- `ProgrammeStatus` - Enum: PLANNED, ACTIVE, COMPLETED, ARCHIVED

**Operations:**
- Create new programmes
- Track programme status transitions
- List programmes with filtering
- Associate programmes with stores/regions

**Events Published:**
- `PROGRAMME_CREATED`
- `PROGRAMME_STARTED`
- `PROGRAMME_COMPLETED`

### Staff Module
**Purpose:** Staff/user management with role-based organization  
**Location:** `src/staff/`

**Key Models:**
- `Staff` - Staff/user entity with role, store assignment
- `StaffRole` - Enum: MANAGER, SUPERVISOR, ASSOCIATE, ANALYST

**Operations:**
- Onboard/offboard staff
- Manage staff roles and permissions
- List staff by store or role
- Update staff assignments

**Events Published:**
- `STAFF_ONBOARDED`
- `STAFF_OFFBOARDED`

### Alerts Module
**Purpose:** Alert triggering and escalation management  
**Location:** `src/alerts/`

**Key Models:**
- `Alert` - Alert entity with severity, status
- `AlertStatus` - Enum: OPEN, ACKNOWLEDGED, RESOLVED
- `AlertSeverity` - Enum: LOW, MEDIUM, HIGH, CRITICAL

**Operations:**
- Create alerts triggered by business events
- Escalate alerts based on age/severity
- Track alert acknowledgment and resolution
- Filter alerts by status/severity

**Events Published:**
- `SLA_BREACH` - When alert SLA is exceeded
- `CRITICAL_ALERT` - When critical alert is triggered
- `ESCALATION_NEEDED` - When escalation threshold reached

**Events Subscribed To:**
- `TASK_OVERDUE` - Trigger alert
- `PROGRAMME_COMPLETED` - Check for pending alerts

### Reports Module
**Purpose:** Analytics and reporting engine  
**Location:** `src/reports/`

**Key Models:**
- `Report` - Report entity with type, scope, period
- `ReportType` - Enum: STORE_SUMMARY, REGIONAL_SUMMARY, DEPARTMENT_PERFORMANCE, ACTIVITY_METRICS, COMPLIANCE_REPORT
- `ReportStatus` - Enum: DRAFT, GENERATED, PUBLISHED

**Operations:**
- Generate reports from operational data
- Retrieve historical reports
- List reports with filtering by type
- Export report data

**Constraints:** ⚠️ **READ-ONLY module** - Reports only consume data, never modify operational state

---

## 3. Architecture Overview

StoreOps uses a **Layered Hexagonal Architecture** with strict unidirectional dependencies:

```
┌─────────────────────────────────┐
│     HTTP Layer (Routes)         │  ← Handles HTTP requests/responses
│  /api/v1/{module}/{resource}    │
└──────────────┬──────────────────┘
               │ calls
               ↓
┌─────────────────────────────────┐
│   Business Logic (Services)     │  ← Business rules & validation
│   {Module}Service               │
└──────────────┬──────────────────┘
               │ calls
               ↓
┌─────────────────────────────────┐
│    Data Access (Repositories)   │  ← CRUD & persistence
│   {Module}Repository            │
└─────────────────────────────────┘
```

### Layer Responsibilities

#### Routes Layer (`src/{module}/routes.py`)
- **Only responsibility:** HTTP request/response handling
- Validates incoming requests via Pydantic models
- Maps HTTP methods to business operations
- Catches `AppError` exceptions and converts to `HTTPException`
- Never contains business logic
- Never calls repositories directly

**Example Endpoint:**
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

#### Service Layer (`src/{module}/service.py`)
- **Owns:** All business logic, validation, orchestration
- Calls repositories for data access
- Publishes domain events via EventBus
- Raises `AppError` or subclasses (never raw exceptions)
- Can read from other modules' services (read-only)
- Manages transaction boundaries

**Example Business Logic:**
```python
async def create_task(
    self,
    task_create: TaskCreate,
    current_user_id: str | None = None,
) -> Task:
    # Validation
    if not task_create.title or not task_create.title.strip():
        raise ValidationError(message="Task title is required")
    
    # Persist
    task = await self.repository.create(
        task_create=task_create,
        created_by=current_user_id,
    )
    
    # Publish event
    await self.event_bus.publish(
        EventType.TASK_CREATED,
        {"task_id": task.id, "title": task.title},
    )
    
    return task
```

#### Repository Layer (`src/{module}/repository.py`)
- **Owns:** Direct data access only
- No business logic
- No external service calls
- Returns domain models (Pydantic), not raw dicts
- Implements CRUD operations with pagination
- Provides `reset()` method for testing

**Example CRUD:**
```python
async def create(self, task_create: TaskCreate, created_by: str | None = None) -> Task:
    """Create new task."""
    self._counter += 1
    task_id = f"task_{self._counter}"
    now = datetime.now(UTC)
    
    task_data = {
        "id": task_id,
        "title": task_create.title,
        "status": task_create.status,
        "created_at": now,
        "updated_at": now,
        "created_by": created_by,
    }
    
    self._tasks[task_id] = task_data
    return Task.model_validate(task_data)
```

---

## 4. Shared Infrastructure

All modules depend on shared infrastructure in `src/shared/`:

### Error Hierarchy (`src/shared/errors.py`)

All errors are instances of `AppError` or its subclasses. Raw exceptions are **never** raised from services.

**Error Codes:**
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

**Error Types:**

1. **ValidationError** (422 Unprocessable Entity)
   ```python
   raise ValidationError(message="Task title is required")
   ```

2. **NotFoundError** (404 Not Found)
   ```python
   raise NotFoundError(resource_type="Task", resource_id=task_id)
   ```

3. **BusinessRuleViolationError** (400 Bad Request)
   ```python
   raise BusinessRuleViolationError(
       message="Cannot mark task as done without completion date",
       rule_name="TASK_COMPLETION_REQUIRES_DATE"
   )
   ```

4. **ConflictError** (409 Conflict)
   ```python
   raise ConflictError(
       resource_type="Staff",
       message="Staff member with email already exists"
   )
   ```

### EventBus (`src/shared/event_bus.py`)

In-memory publish-subscribe system for cross-module communication without direct coupling.

**Pattern:**
- Modules publish domain events
- Other modules subscribe without knowing about each other
- Example: Activities publishes `TASK_CREATED` → Alerts subscribes and triggers escalations

**Standard Events:**
```python
class EventType(StrEnum):
    # Activities
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_OVERDUE = "TASK_OVERDUE"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    
    # Programmes
    PROGRAMME_CREATED = "PROGRAMME_CREATED"
    PROGRAMME_STARTED = "PROGRAMME_STARTED"
    PROGRAMME_COMPLETED = "PROGRAMME_COMPLETED"
    
    # Staff
    STAFF_ONBOARDED = "STAFF_ONBOARDED"
    STAFF_OFFBOARDED = "STAFF_OFFBOARDED"
    
    # Alerts
    SLA_BREACH = "SLA_BREACH"
    CRITICAL_ALERT = "CRITICAL_ALERT"
    ESCALATION_NEEDED = "ESCALATION_NEEDED"
    
    # Reports
    REPORT_GENERATED = "REPORT_GENERATED"
```

**Publishing:**
```python
await self.event_bus.publish(
    EventType.TASK_CREATED,
    {
        "task_id": task.id,
        "title": task.title,
        "priority": task.priority,
    },
)
```

**Subscribing:**
```python
async def handle_task_created(payload: dict) -> None:
    task_id = payload["task_id"]
    # React to event

event_bus.subscribe(EventType.TASK_CREATED, handle_task_created)
```

### Pydantic Models (`src/{module}/models.py`)

Data validation and serialization using Pydantic v2.

**Organization within models.py:**
1. Enums (TaskStatus, TaskPriority, etc.)
2. Base models (TaskBase)
3. Request models (TaskCreate, TaskUpdate)
4. Response models (Task)
5. List/pagination models (TaskList)

**Example:**
```python
class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    category: TaskCategory = Field(...)

class TaskCreate(TaskBase):
    pass  # Inherits all fields from TaskBase

class Task(TaskBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class TaskList(BaseModel):
    items: list[Task]
    total: int
    skip: int
    limit: int
```

### FastAPI Application (`src/main.py`)

Central application factory with route registration and global exception handling.

```python
app = FastAPI(
    title="StoreOps API",
    description="Retail Operations Management REST API",
    version="0.1.0",
)

# Global exception handler
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

# Router inclusion
app.include_router(activities_router)
app.include_router(programmes_router)
app.include_router(staff_router)
app.include_router(alerts_router)
app.include_router(reports_router)
```

---

## 5. Dependency Flow

### Valid Dependencies (✅ Allowed)

```
Routes → Services
Services → Repositories
Services → EventBus
Services → Other Services (read-only)
All → Shared errors & models
All → EventBus
```

### Invalid Dependencies (❌ Prohibited)

```
Routes → Repositories (must go through service)
Repositories → Services (circular dependency)
Repositories → EventBus (no side effects at data layer)
Circular imports within modules
```

### Module-to-Module Communication

**Pattern:** EventBus only, never direct service calls

```
Activities Service publishes TASK_CREATED
                ↓
            EventBus (global singleton)
                ↓
Alerts Service subscribes to TASK_CREATED
Alerts reacts without knowing Activities exists
```

---

## 6. Existing Testing Framework

### Tools
- **Framework:** Pytest with pytest-asyncio
- **HTTP Client:** FastAPI TestClient
- **Location:** `tests/` directory

### Shared Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset all state before each test."""
    reset_event_bus()
    get_activities_repository().reset()
    get_programmes_repository().reset()
    get_staff_repository().reset()
    get_alerts_repository().reset()
    get_reports_repository().reset()
    yield
    # Cleanup after test
```

### Test Organization

```python
class TestActivitiesRoutes:
    """Tests for activities routes."""
    
    def test_create_task(self, client: TestClient) -> None:
        """Test creating a task."""
        task_data = {...}
        response = client.post("/api/v1/activities/tasks", json=task_data)
        assert response.status_code == 201
        assert response.json()["title"] == "Test Task"
    
    def test_get_task(self, client: TestClient) -> None:
        """Test getting a task."""
        # Setup
        create_response = client.post("/api/v1/activities/tasks", json={...})
        task_id = create_response.json()["id"]
        
        # Execute
        response = client.get(f"/api/v1/activities/tasks/{task_id}")
        
        # Verify
        assert response.status_code == 200
```

### Event Verification in Tests

```python
def test_task_creation_publishes_event(self, client: TestClient) -> None:
    client.post("/api/v1/activities/tasks", json={...})
    
    from src.shared.event_bus import get_event_bus
    event_bus = get_event_bus()
    history = event_bus.get_event_history()
    
    assert len(history) > 0
    assert history[0][0] == EventType.TASK_CREATED
```

---

## 7. Important Repository Paths

```
StoreOpsAPI/StoreOps/
├── src/
│   ├── main.py                 # Application factory
│   ├── activities/             # Task management module
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── repository.py
│   ├── programmes/             # Programme management module
│   ├── staff/                  # Staff management module
│   ├── alerts/                 # Alert management module
│   ├── reports/                # Reporting module (read-only)
│   └── shared/
│       ├── errors.py           # Error hierarchy
│       ├── event_bus.py        # EventBus implementation
│       └── dependencies.py     # FastAPI dependency injection
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_activities.py
│   ├── test_programmes.py
│   ├── test_staff.py
│   ├── test_alerts.py
│   ├── test_reports.py
│   ├── test_errors.py
│   └── test_event_bus.py
├── docs/
│   └── repository-assessment.md # Architecture documentation
├── pyproject.toml              # Project configuration
├── requirements.txt            # Dependencies
└── Dockerfile                  # Container configuration
```

---

## 8. Current Coding Standards

### Python Version
**Minimum:** Python 3.12+

### Code Style
- **Linter:** Ruff
- **Line Length:** 100 characters
- **Type Checking:** Mypy (strict mode)
- **Async:** All I/O is async/await

### Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Classes | PascalCase | `ActivitiesService`, `NotFoundError` |
| Functions/Methods | lowercase_with_underscores | `create_task()`, `get_by_id()` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `MAX_PAGE_SIZE = 100` |
| Private/Protected | Prefix with `_` | `_event_bus`, `_handlers` |
| Modules | lowercase_with_underscores | `activities/`, `event_bus.py` |

### Type Hints
**Required everywhere.** All functions must have full type annotations:

```python
async def create_task(
    self,
    task_create: TaskCreate,
    current_user_id: str | None = None,
) -> Task:
    pass
```

### Async/Await
All I/O operations (database, external services, events) use async/await:

```python
async def get_task(self, task_id: str) -> Task:
    task = await self.repository.get_by_id(task_id)
    return task
```

### Docstrings
All public functions and classes have docstrings:

```python
async def create_task(self, task_create: TaskCreate) -> Task:
    """Create new task with validation.
    
    Args:
        task_create: Task creation data
    
    Returns:
        Created task
    
    Raises:
        ValidationError: If validation fails
    """
```

### Import Ordering
1. Standard library
2. Third-party imports
3. Internal imports

```python
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.activities.models import Task
from src.shared.errors import ValidationError
```

---

## 9. Reports Module Constraints

The Reports module has special constraints to maintain data integrity:

### ⚠️ Constraint: READ-ONLY
- Reports module **never modifies** operational state
- Report service can **read** from other modules' repositories
- Report service **never publishes events** (no side effects)
- Report creation is metadata only; actual data aggregation is future work

### Why?
- Prevents reports from accidentally corrupting operational data
- Ensures reports are safe to regenerate without side effects
- Maintains clear separation between analytics and operations

### Example - Safe Pattern:
```python
# ✅ GOOD: Reports reads from other services/repositories
class ReportsService:
    async def generate_activity_report(self, ...):
        # Can read activities
        activities, total = await activities_repo.list_all()
        # Process and aggregate
        return report

# ❌ BAD: Reports modifying state
class ReportsService:
    async def generate_report(self, ...):
        await activities_repo.update(...)  # Forbidden!
        await self.event_bus.publish(...)  # Forbidden!
```

---

## Quick Reference

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

# Health check
curl http://localhost:8000/health
```

### Key Files by Purpose

| Purpose | File |
|---------|------|
| HTTP routes | `src/{module}/routes.py` |
| Business logic | `src/{module}/service.py` |
| Data access | `src/{module}/repository.py` |
| Data models | `src/{module}/models.py` |
| Error handling | `src/shared/errors.py` |
| Event publishing | `src/shared/event_bus.py` |
| Testing fixtures | `tests/conftest.py` |
| Application setup | `src/main.py` |

### API Endpoints Pattern

```
POST   /api/v1/{module}/{resource}        # Create
GET    /api/v1/{module}/{resource}        # List
GET    /api/v1/{module}/{resource}/{id}   # Read
PUT    /api/v1/{module}/{resource}/{id}   # Update
DELETE /api/v1/{module}/{resource}/{id}   # Delete
```

---

## When to Use This Skill

Load this skill when:
- **Starting new feature development** - Understand module structure and patterns
- **Joining the team** - Onboard quickly to the codebase
- **Cross-module work** - Understand module boundaries and communication
- **Debugging issues** - Know where code lives and how layers interact
- **Adding new modules** - Follow established patterns

---

*This skill encodes the essential context for contributing to StoreOps. For architectural governance rules, see [[architecture-principles]]. For testing patterns, see [[how-to-test]].*
