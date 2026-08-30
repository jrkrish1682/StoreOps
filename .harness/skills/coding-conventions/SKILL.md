# StoreOps Coding Conventions

**Version:** 1.0.0  
**Last Updated:** 2026-08-29  
**Scope:** StoreOps Python 3.12+ FastAPI Application

---

## Purpose

This skill documents the coding standards, naming conventions, and code organization patterns used in the StoreOps codebase. Every rule has been validated against existing code.

**Use this skill when:**
- Writing new code to match existing style
- Setting expectations for pull requests
- Configuring IDE tooling
- Onboarding new contributors

---

## 1. Python Typing Standards

### Rule: All Functions Must Have Type Hints

**Mypy Configuration:** `disallow_untyped_defs = true`

Every function and method must have complete type annotations on parameters and return values.

#### Example ✅

**File:** `src/activities/service.py:79`

```python
async def get_task(self, task_id: str) -> Task:
    """Get task by ID.

    Args:
        task_id: Task ID

    Returns:
        Task

    Raises:
        NotFoundError: If task not found
    """
    task = await self.repository.get_by_id(task_id)
    if not task:
        raise NotFoundError(resource_type="Task", resource_id=task_id)
    return task
```

#### Anti-pattern ❌

```python
# ❌ Missing return type
async def get_task(self, task_id):
    pass

# ❌ Incomplete annotations
async def create_task(self, task_create: TaskCreate):
    pass

# ❌ Using `Any` without justification
from typing import Any

async def process_data(self, data: Any) -> Any:
    pass
```

### Rule: Optional Types Use Union Syntax

Use `Type | None` instead of `Optional[Type]` (Python 3.12+ syntax).

#### Example ✅

```python
assigned_user_id: str | None = None
due_date: datetime | None = None
details: dict[str, Any] | None = None
```

#### Anti-pattern ❌

```python
from typing import Optional

assigned_user_id: Optional[str] = None  # ❌ Old syntax
```

### Rule: Generic Collections Must Be Typed

All collections must specify their element types.

#### Example ✅

```python
items: list[Task]
mapping: dict[str, int]
tuple_data: tuple[str, int, bool]
data: dict[str, Any]
handlers: list[EventHandler]
```

#### Anti-pattern ❌

```python
items: list  # ❌ Missing element type
mapping: dict  # ❌ Missing key/value types
```

---

## 2. FastAPI Conventions

### Rule: Routers Use Consistent Path Prefixes

All routers follow the pattern: `/api/v1/{module}` with lowercase module names.

#### Example ✅

**File:** `src/activities/routes.py:17`

```python
router = APIRouter(
    prefix="/api/v1/activities",
    tags=["activities"],
)
```

#### Anti-pattern ❌

```python
# ❌ Missing /api/v1 prefix
router = APIRouter(prefix="/activities")

# ❌ Using uppercase
router = APIRouter(prefix="/api/v1/Activities")

# ❌ Missing tags
router = APIRouter(prefix="/api/v1/activities")
```

### Rule: Dependency Injection via `Depends()`

All route handlers use FastAPI's `Depends()` for dependency injection.

#### Example ✅

**File:** `src/activities/routes.py:28`

```python
@router.post(
    "/tasks",
    response_model=Task,
    status_code=201,
)
async def create_task(
    task_create: TaskCreate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Create new task."""
    try:
        return await service.create_task(task_create=task_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

#### Anti-pattern ❌

```python
# ❌ Manually instantiating service
@router.post("/tasks")
async def create_task(task_create: TaskCreate) -> Task:
    service = get_activities_service()  # ❌ Wrong!
    return await service.create_task(task_create)

# ❌ Missing response_model
@router.post("/tasks")
async def create_task(task_create: TaskCreate):
    pass
```

### Rule: Query Parameters Use `Query()` with Constraints

All query parameters must use FastAPI's `Query()` with validation constraints.

#### Example ✅

**File:** `src/activities/routes.py:80`

```python
@router.get(
    "/tasks",
    response_model=TaskList,
)
async def list_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ActivitiesService = Depends(get_activities_service),
) -> TaskList:
    result = await service.list_tasks(skip=skip, limit=limit)
    return TaskList(**result)
```

#### Anti-pattern ❌

```python
# ❌ Query params without constraints
async def list_tasks(skip: int = 0, limit: int = 10):
    pass

# ❌ No Query() wrapper
async def list_tasks(
    skip: int = Query(0),  # Missing constraints
    limit: int = 10,  # Not using Query()
):
    pass
```

### Rule: HTTP Status Codes Are Explicit

All route handlers explicitly specify status codes via `status_code` parameter.

#### Example ✅

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(...) -> Task:
    pass

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(...) -> None:
    pass

@router.get("/tasks", response_model=TaskList)
async def list_tasks(...) -> TaskList:  # Default 200
    pass
```

#### Anti-pattern ❌

```python
# ❌ Missing explicit status code
@router.post("/tasks", response_model=Task)
async def create_task(...) -> Task:
    pass
```

---

## 3. Pydantic Model Patterns

### Rule: Models Organized by Concern

Models within `models.py` are organized in this order:
1. Enums
2. Base models
3. Request models (Create, Update)
4. Response models
5. List/pagination models

#### Example ✅

**File:** `src/activities/models.py`

```python
# 1. Enums
class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"

# 2. Base model
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    category: TaskCategory = Field(...)

# 3. Request models
class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    status: TaskStatus | None = None

# 4. Response model
class Task(TaskBase):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    model_config = {"from_attributes": True}

# 5. List model
class TaskList(BaseModel):
    items: list[Task]
    total: int
    skip: int
    limit: int
```

#### Anti-pattern ❌

```python
# ❌ Random ordering (enums mixed with models)
class Task(BaseModel):
    pass

class TaskStatus(StrEnum):
    pass

# ❌ All in one model
class TaskCreateRequest(BaseModel):
    title: str

class TaskUpdateRequest(BaseModel):
    title: str
```

### Rule: Field Validation Using Pydantic

Use Pydantic's `Field()` for all validation constraints.

#### Example ✅

```python
title: str = Field(..., min_length=1, max_length=200)
priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
category: TaskCategory = Field(...)  # Required, no default
assigned_user_id: str | None = None
limit: int = Query(default=10, ge=1, le=100)
```

#### Anti-pattern ❌

```python
# ❌ No validation
title: str

# ❌ Validation in service instead of model
class TaskCreate(BaseModel):
    title: str  # Should have min_length, max_length
```

### Rule: Response Models Include `model_config`

Response models should include `from_attributes = True` to support ORM mapping (future SQLAlchemy).

#### Example ✅

```python
class Task(TaskBase):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}
```

---

## 4. Import Ordering

### Rule: Three-Section Import Organization

Imports organized in three groups, separated by blank lines:
1. Standard library
2. Third-party packages
3. Internal imports (src.*)

#### Example ✅

**File:** `src/activities/service.py:14`

```python
# Standard library
from typing import Any

# Third-party
from pydantic import BaseModel

# Internal imports
from src.activities.models import Task, TaskCreate, TaskStatus
from src.activities.repository import ActivitiesRepository
from src.shared.errors import NotFoundError, ValidationError
from src.shared.event_bus import EventBus, EventType
```

#### Anti-pattern ❌

```python
# ❌ Mixed ordering
from pydantic import BaseModel
from src.activities.models import Task
from typing import Any
import os
from src.shared.errors import NotFoundError

# ❌ No blank line separation
from typing import Any
from pydantic import BaseModel
from src.activities.models import Task
```

---

## 5. Naming Conventions

### Classes: PascalCase

All class names use PascalCase.

#### Example ✅

```python
class ActivitiesService:
    pass

class TaskRepository:
    pass

class NotFoundError(AppError):
    pass

class EventBus:
    pass
```

#### Anti-pattern ❌

```python
class activities_service:  # ❌ lowercase
    pass

class Task_Repository:  # ❌ Mixed case
    pass
```

### Functions/Methods: lowercase_with_underscores

All functions and methods use lowercase_with_underscores.

#### Example ✅

```python
async def create_task(self, task_create: TaskCreate) -> Task:
    pass

async def get_task(self, task_id: str) -> Task:
    pass

async def list_by_status(self, status: str) -> tuple[list[Task], int]:
    pass

def reset(self) -> None:
    pass
```

#### Anti-pattern ❌

```python
async def createTask(self, task_create):  # ❌ camelCase
    pass

async def GetTask(self, task_id):  # ❌ PascalCase
    pass
```

### Constants: UPPERCASE_WITH_UNDERSCORES

All module-level constants use UPPERCASE_WITH_UNDERSCORES.

#### Example ✅

```python
DEFAULT_SKIP = 0
DEFAULT_LIMIT = 10
MAX_PAGE_SIZE = 100
```

#### Anti-pattern ❌

```python
default_skip = 0  # ❌ Lowercase
DEFAULT_skip = 0  # ❌ Mixed case
```

### Private/Protected: Prefix with `_`

Private and protected members prefix with underscore.

#### Example ✅

```python
class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._event_history: list[tuple[str, dict[str, Any]]] = []

_repository: ActivitiesRepository | None = None

def _internal_helper() -> None:
    pass
```

#### Anti-pattern ❌

```python
class EventBus:
    def __init__(self) -> None:
        self.handlers = {}  # ❌ Should be _handlers
        self.event_history = []  # ❌ Should be _event_history

repository: ActivitiesRepository | None = None  # ❌ Should be _repository
```

### Modules: lowercase_with_underscores

Module and package names are lowercase with underscores.

#### Example ✅

```
src/
    activities/
    event_bus.py
    shared_errors.py  # If multi-word
```

#### Anti-pattern ❌

```
src/
    Activities/  # ❌ PascalCase
    EventBus.py  # ❌ PascalCase
```

---

## 6. Error Handling

### Rule: Never Raise Raw Exceptions

Services and routes must **only** raise `AppError` or its subclasses. Raw exceptions (`ValueError`, `RuntimeError`, `Exception`) are prohibited.

#### Example ✅

**File:** `src/activities/service.py:54`

```python
# Validation error
if not task_create.title or not task_create.title.strip():
    raise ValidationError(message="Task title is required")

# Not found error
task = await self.repository.get_by_id(task_id)
if not task:
    raise NotFoundError(resource_type="Task", resource_id=task_id)
```

#### Anti-pattern ❌

```python
# ❌ ValueError (raw exception)
if not task_create.title:
    raise ValueError("Title is required")

# ❌ RuntimeError
if not task:
    raise RuntimeError("Task not found")

# ❌ Generic Exception
raise Exception("Something went wrong")
```

### Rule: Routes Catch AppError

Routes catch `AppError` exceptions and convert to `HTTPException` with structured error responses.

#### Example ✅

**File:** `src/activities/routes.py:44`

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

#### Anti-pattern ❌

```python
# ❌ Catching generic Exception
try:
    task = await service.create_task(task_create)
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ❌ No error handling
@router.post("/tasks")
async def create_task(task_create: TaskCreate) -> Task:
    return await service.create_task(task_create)  # Unhandled errors leak
```

---

## 7. Logging Conventions

### Rule: Use Standard Python Logging

Use Python's built-in `logging` module for all logging. No `print()` statements.

#### Example ✅

```python
import logging

logger = logging.getLogger(__name__)

async def create_task(self, task_create: TaskCreate) -> Task:
    logger.debug(f"Creating task: {task_create.title}")
    task = await self.repository.create(task_create)
    logger.info(f"Task created: {task.id}")
    return task
```

#### Anti-pattern ❌

```python
# ❌ print() statements
print(f"Creating task: {task_create.title}")

# ❌ No structured logging
print(f"Error: {e}")
```

### Rule: Log Levels

- **DEBUG:** Detailed internal flows, variable values
- **INFO:** Important state changes, completed operations
- **WARNING:** Recoverable errors, deprecated paths
- **ERROR:** Exceptions, failure conditions
- **CRITICAL:** System shutdown conditions

#### Example ✅

```python
logger.debug("Processing started")
logger.info("Task created successfully")
logger.warning("Retry attempt 2 of 3")
logger.error("Failed to persist task", exc_info=True)
logger.critical("Database connection lost")
```

---

## 8. Dependency Injection

### Rule: Constructor-Based DI

All dependencies injected via constructor parameters. Factories manage singletons.

#### Example ✅

**File:** `src/activities/service.py:20`

```python
class ActivitiesService:
    def __init__(
        self,
        repository: ActivitiesRepository,
        event_bus: EventBus,
    ) -> None:
        self.repository = repository
        self.event_bus = event_bus
```

#### Anti-pattern ❌

```python
# ❌ Global variable injection
service = get_activities_service()  # In method

class MyService:
    def __init__(self):
        self.repository = get_activities_repository()  # ❌ Wrong

# ❌ Hardcoded dependencies
class MyService:
    def __init__(self):
        self.repository = ActivitiesRepository()  # Not injected
```

### Rule: Factory Pattern for Singletons

Module-level factories manage singleton instances.

#### Example ✅

**File:** `src/activities/repository.py`

```python
_repository: ActivitiesRepository | None = None

def get_activities_repository() -> ActivitiesRepository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = ActivitiesRepository()
    return _repository
```

#### Anti-pattern ❌

```python
# ❌ Creating new instance each time
def get_activities_repository() -> ActivitiesRepository:
    return ActivitiesRepository()  # New instance!

# ❌ Module-level instantiation
_repository = ActivitiesRepository()  # Not lazy-loaded
```

---

## 9. Service Layer Practices

### Rule: Service Owns Validation

All business validation happens in services, never in routes or repositories.

#### Example ✅

**File:** `src/activities/service.py:54`

```python
async def create_task(
    self,
    task_create: TaskCreate,
    current_user_id: str | None = None,
) -> Task:
    # Validation in service
    if not task_create.title or not task_create.title.strip():
        raise ValidationError(message="Task title is required")
    
    task = await self.repository.create(task_create, current_user_id)
    # ... publish event
    return task
```

#### Anti-pattern ❌

```python
# ❌ Validation in route
@router.post("/tasks")
async def create_task(task_create: TaskCreate, service: ActivitiesService) -> Task:
    if not task_create.title:  # ❌ Should be in service
        raise HTTPException(status_code=422)
    return await service.create_task(task_create)
```

### Rule: Services Are Async

All service methods use `async`/`await`. All I/O is async.

#### Example ✅

```python
class ActivitiesService:
    async def create_task(self, task_create: TaskCreate) -> Task:
        task = await self.repository.create(task_create)
        await self.event_bus.publish(EventType.TASK_CREATED, {...})
        return task
```

#### Anti-pattern ❌

```python
# ❌ Synchronous service methods
class ActivitiesService:
    def create_task(self, task_create: TaskCreate) -> Task:  # Missing async
        pass

# ❌ Missing await
async def create_task(self, task_create: TaskCreate) -> Task:
    task = self.repository.create(task_create)  # Missing await
    return task
```

---

## 10. Repository Layer Practices

### Rule: Pagination Returns `tuple[list[Model], int]`

All `list_*` methods return a tuple: `(list of items, total count)`.

#### Example ✅

**File:** `src/activities/repository.py:68`

```python
async def list_all(
    self,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[Task], int]:
    """List all tasks with pagination."""
    all_tasks = list(self._tasks.values())
    total = len(all_tasks)
    tasks = all_tasks[skip : skip + limit]
    return [Task.model_validate(t) for t in tasks], total
```

#### Anti-pattern ❌

```python
# ❌ Just returning list
async def list_all(self, skip: int = 0, limit: int = 10) -> list[Task]:
    pass

# ❌ Returning dict instead of tuple
async def list_all(self) -> dict:
    return {"items": tasks, "total": total}
```

### Rule: Repository Returns Domain Models

Repositories always return Pydantic models, never raw dicts.

#### Example ✅

```python
async def get_by_id(self, task_id: str) -> Task | None:
    task_data = self._tasks.get(task_id)
    return Task.model_validate(task_data) if task_data else None
```

#### Anti-pattern ❌

```python
# ❌ Returning raw dict
async def get_by_id(self, task_id: str) -> dict:
    return self._tasks.get(task_id)

# ❌ Not validating through model
async def get_by_id(self, task_id: str) -> Task:
    return self._tasks[task_id]  # Direct access, not validated
```

### Rule: Repository Provides `reset()` Method

All repositories must have a `reset()` method for testing.

#### Example ✅

```python
def reset(self) -> None:
    """Reset repository (clear all data)."""
    self._tasks.clear()
    self._counter = 0
```

---

## 11. EventBus Usage Patterns

### Rule: Events Published Asynchronously

Event publishing is `async` and awaited in services.

#### Example ✅

**File:** `src/activities/service.py:67`

```python
async def create_task(self, task_create: TaskCreate) -> Task:
    task = await self.repository.create(task_create, current_user_id)
    
    # Publish event asynchronously
    await self.event_bus.publish(
        EventType.TASK_CREATED,
        {
            "task_id": task.id,
            "title": task.title,
            "priority": task.priority,
        },
    )
    return task
```

#### Anti-pattern ❌

```python
# ❌ Missing await
await self.event_bus.publish(...)  # Actually this is correct
# ❌ But forgetting to await is wrong:
self.event_bus.publish(...)  # No await!
```

### Rule: Event Payload Is Dictionary

Event payloads are always dictionaries with string keys and JSON-serializable values.

#### Example ✅

```python
await self.event_bus.publish(
    EventType.TASK_CREATED,
    {
        "task_id": task.id,  # str
        "title": task.title,  # str
        "priority": task.priority,  # str (enum stringified)
        "due_date": task.due_date.isoformat() if task.due_date else None,  # ISO string
    },
)
```

#### Anti-pattern ❌

```python
# ❌ Passing model object
await self.event_bus.publish(EventType.TASK_CREATED, task)  # ❌ Model not dict

# ❌ Non-serializable values
await self.event_bus.publish(EventType.TASK_CREATED, {
    "task": task,  # ❌ Object
    "created_at": datetime.now(),  # ❌ Not ISO string
})
```

---

## 12. File Organization

### Directory Structure

```
src/
├── {module}/
│   ├── __init__.py
│   ├── models.py       # Data models
│   ├── routes.py       # HTTP endpoints
│   ├── service.py      # Business logic
│   └── repository.py   # Data access
├── shared/
│   ├── __init__.py
│   ├── errors.py       # Error hierarchy
│   ├── event_bus.py    # EventBus
│   └── dependencies.py # DI functions
├── main.py             # Application factory
└── __init__.py
```

### Within Each File

#### models.py
1. Module docstring
2. Imports (stdlib, third-party, internal)
3. Enums
4. Base models
5. Request models
6. Response models
7. List/pagination models

#### service.py
1. Module docstring explaining responsibilities
2. Imports
3. Service class with `__init__`, then public methods
4. Factory function at end

#### repository.py
1. Module docstring explaining responsibilities
2. Imports
3. Repository class with CRUD methods
4. `reset()` method
5. Global singleton instance
6. Factory function

#### routes.py
1. Module docstring explaining responsibilities
2. Imports
3. Router configuration
4. HTTP endpoints (POST, GET, PUT, DELETE)
5. Consistent error handling pattern

---

## 13. Docstring Format

### Module Docstrings

Every module has a docstring at the top describing its purpose and responsibilities.

#### Example ✅

```python
"""
Service layer for Activities module.

Responsibilities:
- Business logic
- Validation
- Orchestration
- Publishing events
- Always raise AppError (never raw exceptions)
- Call repositories only
- May read from other modules' services
"""
```

### Function/Method Docstrings

Every public function has a docstring with Args, Returns, and Raises.

#### Example ✅

```python
async def create_task(
    self,
    task_create: TaskCreate,
    current_user_id: str | None = None,
) -> Task:
    """Create new task with validation.

    Args:
        task_create: Task creation data
        current_user_id: User creating the task

    Returns:
        Created task

    Raises:
        ValidationError: If validation fails
    """
```

---

## 14. Code Quality Principles

### Line Length

Maximum 100 characters per line (enforced by Ruff).

#### Example ✅

```python
async def list_by_status(
    self,
    status: str,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[Task], int]:
    """Line broken to stay under 100 chars."""
```

#### Anti-pattern ❌

```python
# ❌ Line too long (>100 chars)
async def get_tasks_by_status_and_priority_with_pagination(self, status: str, priority: str, skip: int = 0, limit: int = 10):
    pass
```

### No Magic Numbers

All numeric constants are named.

#### Example ✅

```python
DEFAULT_SKIP = 0
DEFAULT_LIMIT = 10
MAX_PAGE_SIZE = 100

skip: int = Query(default=DEFAULT_SKIP, ge=0)
limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_PAGE_SIZE)
```

#### Anti-pattern ❌

```python
skip: int = Query(default=0, ge=0)  # Magic 0
limit: int = Query(default=10, ge=1, le=100)  # Magic numbers
```

---

## Enforcement

### Linting: Ruff

```bash
ruff check src
```

**Configuration:** `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "PIE", "PT", "RUF"]
ignore = ["E501", "B008", "B904"]
```

### Type Checking: Mypy

```bash
mypy src
```

**Configuration:** `pyproject.toml`

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

### Formatting: Ruff Format

```bash
ruff format src
```

---

## Quick Reference

| Category | Convention | Example |
|----------|-----------|---------|
| Classes | PascalCase | `ActivitiesService` |
| Functions | lowercase_with_underscores | `create_task()` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `MAX_PAGE_SIZE` |
| Private | Prefix with `_` | `_event_bus` |
| Modules | lowercase_with_underscores | `event_bus.py` |
| Type hints | All parameters and returns | `async def get(id: str) -> Task:` |
| Optionals | Use `\|` syntax | `str \| None` |
| Line length | Maximum 100 characters | Enforced by Ruff |
| Import order | Stdlib, third-party, internal | 3 sections |
| Errors | AppError only | `raise ValidationError(...)` |
| Async | All I/O is async/await | `await service.create()` |

---

*For architectural principles, see [[architecture-principles]]. For testing patterns, see [[how-to-test]].*
