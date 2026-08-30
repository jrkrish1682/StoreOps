# How to Review StoreOps Generated Code

**Purpose:** Teach the Evaluator how to systematically review generated StoreOps code using a deterministic, sequential process.

## Sequential Review Process

The review must follow these 7 steps in order. Each step validates specific aspects of the implementation.

### Step 1: Review Sprint Contract

**What to check:**
- Sprint ID and objective are clearly stated
- Modules impacted are listed (activities, alerts, programmes, reports, staff, shared)
- Files expected to change are specified (models.py, routes.py, service.py, repository.py)
- Dependencies on other modules are documented
- Architecture constraints are explicit
- Acceptance criteria are in GIVEN/WHEN/THEN format
- Required tests are listed
- Completion evidence is testable

**File to review:** Look for `generator-summary.md` or sprint documentation in the PR

**Verdict:**
- ✅ PASS: All elements present and clear
- ⚠️ REVIEW: Some elements missing or vague
- ❌ FAIL: Contract incomplete or incomprehensible

**Example Pass Contract:**
```
Sprint ID: ACTIVITIES-001
Objective: Add PATCH /api/v1/activities/tasks/{id} endpoint for bulk status updates
Modules Impacted: activities
Files Expected: src/activities/models.py, src/activities/service.py, src/activities/routes.py, tests/test_activities.py
Dependencies: None (internal only)
Architecture Constraints:
- No direct repository calls in routes
- Must publish TASK_STATUS_CHANGED event for each updated task
- Must validate task exists before updating
Acceptance Criteria:
  GIVEN multiple tasks exist with status TODO
  WHEN PATCH /api/v1/activities/tasks/{id} with status=DONE
  THEN task status changes to DONE and TASK_STATUS_CHANGED event is published
Required Tests:
- test_bulk_update_task_status_success
- test_bulk_update_nonexistent_task_returns_404
- test_bulk_update_invalid_status_returns_422
```

---

### Step 2: Review generator-summary.md

**What to check:**
- High-level summary of changes (what problem does this solve?)
- List of files modified or created
- Key decisions and rationale
- Event handling (if any)
- Error scenarios handled
- Test coverage approach

**File to review:** `generator-summary.md` in the submission

**Verdict:**
- ✅ PASS: Clear summary, decisions documented, all files listed
- ⚠️ REVIEW: Summary present but incomplete
- ❌ FAIL: No summary or summary is unclear

**Checklist:**
- [ ] Problem statement is clear
- [ ] Files listed match sprint contract
- [ ] Key design decisions explained
- [ ] Event publishing documented (if needed)
- [ ] Error handling strategy stated
- [ ] Test approach described

---

### Step 3: Review Source Code Changes

**What to check:**

#### A. File Organization & Naming
- [ ] Files follow naming convention (lowercase_with_underscores)
- [ ] Classes use PascalCase (e.g., `ActivitiesService`, `TaskRepository`)
- [ ] Functions use lowercase_with_underscores (e.g., `create_task`, `get_by_id`)
- [ ] Constants use UPPERCASE_WITH_UNDERSCORES (e.g., `MAX_TASKS = 100`)
- [ ] Private members prefixed with `_` (e.g., `_repository`, `_handlers`)

#### B. Route Layer (`routes.py`)

**Responsibilities:**
- HTTP request/response handling only
- Request validation via Pydantic models
- Dependency injection via `Depends()`
- No business logic
- No direct repository access

**Code Pattern:**
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

**Violations to flag:**
- ❌ Business logic in routes
- ❌ Direct repository calls (should go through service)
- ❌ Raw Exception handling (must catch AppError)
- ❌ Response formatting logic (should be in Pydantic models)
- ❌ Manual error responses (must use AppError)

**File-level feedback template:**
```
✅ routes.py: Correct
- All endpoints use Depends() for dependency injection
- All exceptions caught as AppError
- No business logic in route handlers
```

#### C. Service Layer (`service.py`)

**Responsibilities:**
- All business logic & domain rules
- Input validation (beyond Pydantic)
- Orchestration across repositories
- Event publishing
- Always raise `AppError` or subclasses
- Call repositories only (never other services directly)
- Database transaction boundaries

**Code Pattern:**
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
        
        # Publish event
        await self.event_bus.publish(EventType.TASK_CREATED, {...})
        return task

async def get_activities_service() -> ActivitiesService:
    repository = get_activities_repository()
    event_bus = get_event_bus()
    return ActivitiesService(repository=repository, event_bus=event_bus)
```

**Violations to flag:**
- ❌ Circular service imports
- ❌ Raw exceptions (ValueError, RuntimeError, etc.)
- ❌ Direct service-to-service coupling (must use events)
- ❌ Missing event publishing (check EventBus requirement)
- ❌ Repository import in any file except service.py (violates dependency direction)
- ❌ Synchronous I/O (all must be async)

**File-level feedback template:**
```
✅ service.py: Architecture compliant
- All exceptions are AppError subclasses
- Event published for TASK_CREATED
- No circular dependencies
- Proper dependency injection in __init__
```

#### D. Repository Layer (`repository.py`)

**Responsibilities:**
- Direct data access only
- No business logic
- No external service calls
- No service imports (circular dependency prevention)
- CRUD operations
- Pagination (returns `tuple[list[Model], int]`)
- Testing helpers (reset method)

**Code Pattern:**
```python
class ActivitiesRepository:
    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, task_create: TaskCreate) -> Task:
        self._counter += 1
        task_id = f"task_{self._counter}"
        task_data = {...}
        self._tasks[task_id] = task_data
        return Task.model_validate(task_data)

    async def list_all(self, skip: int = 0, limit: int = 10) -> tuple[list[Task], int]:
        all_tasks = list(self._tasks.values())
        total = len(all_tasks)
        tasks = all_tasks[skip : skip + limit]
        return [Task.model_validate(t) for t in tasks], total

    def reset(self) -> None:
        self._data.clear()
        self._counter = 0

_repository: ActivitiesRepository | None = None

def get_activities_repository() -> ActivitiesRepository:
    global _repository
    if _repository is None:
        _repository = ActivitiesRepository()
    return _repository
```

**Violations to flag:**
- ❌ Service imports
- ❌ Business logic (should raise ValidationError in service, not repo)
- ❌ Event publishing (must be in service)
- ❌ Direct external API calls (should be in service)

**File-level feedback template:**
```
✅ repository.py: Clean data access layer
- No service imports
- No business logic
- Proper pagination pattern
- Reset method for testing
```

#### E. Models Layer (`models.py`)

**Code Pattern:**
```python
"""Data models for Activities module."""

from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field

# 1. Enums first
class TaskStatus(StrEnum):
    TODO = "TODO"
    DONE = "DONE"

# 2. Base models
class TaskBase(BaseModel):
    title: str
    status: TaskStatus

# 3. Request models
class TaskCreate(TaskBase):
    pass

# 4. Response models
class Task(TaskBase):
    id: str
    created_at: datetime

# 5. List/pagination models
class TaskList(BaseModel):
    items: list[Task]
    total: int
```

**Violations to flag:**
- ❌ Business logic in models
- ❌ Circular model imports
- ❌ Missing type hints on fields

**File-level feedback template:**
```
✅ models.py: Well-organized
- Enums defined first
- Clean inheritance hierarchy
- All fields properly typed
```

---

### Step 4: Review Test Coverage

**What to check:**

#### Test Organization
- [ ] Tests organized by class (TestActivitiesRoutes, TestActivitiesService, etc.)
- [ ] Naming convention: `test_<function>_<scenario>`
- [ ] AAA pattern used (Arrange, Act, Assert)
- [ ] Async tests marked with `@pytest.mark.asyncio`

#### Test Categories

**A. Integration Tests (in routes)**
- [ ] Create endpoint test (POST)
- [ ] Get endpoint test (GET by ID)
- [ ] List endpoint test (GET all)
- [ ] Update endpoint test (PUT/PATCH)
- [ ] Delete endpoint test (DELETE)
- [ ] Filter/search endpoint tests (if applicable)

**B. Error Path Tests**
- [ ] 404 Not Found scenario
- [ ] 422 Validation error scenario
- [ ] 409 Conflict (duplicate) scenario
- [ ] 400 Business rule violation scenario

**C. Event Verification Tests**
- [ ] Event published on success
- [ ] Event history checked
- [ ] Event payload contains required fields

**Example Test Pattern:**
```python
class TestActivitiesRoutes:
    def test_create_task_success(self, client: TestClient) -> None:
        """Test creating a task successfully."""
        # Arrange
        task_data = {
            "title": "Test Task",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.HIGH,
        }
        
        # Act
        response = client.post("/api/v1/activities/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert "id" in data

    def test_create_task_missing_title(self, client: TestClient) -> None:
        """Test validation when title is missing."""
        task_data = {"status": TaskStatus.TODO}
        response = client.post("/api/v1/activities/tasks", json=task_data)
        assert response.status_code == 422

    def test_create_task_publishes_event(self, client: TestClient) -> None:
        """Test that task creation publishes TASK_CREATED event."""
        from src.shared.event_bus import get_event_bus
        
        event_bus = get_event_bus()
        task_data = {"title": "Test Task", "status": TaskStatus.TODO}
        
        client.post("/api/v1/activities/tasks", json=task_data)
        
        history = event_bus.get_event_history()
        assert len(history) > 0
        assert history[0][0] == EventType.TASK_CREATED
```

**Violations to flag:**
- ❌ No error path tests
- ❌ Event not verified in integration tests
- ❌ Missing reset_state fixture autouse
- ❌ Synchronous async tests (missing @pytest.mark.asyncio)

**File-level feedback template:**
```
✅ test_activities.py: Good coverage
- Tests for create, get, list, update, delete
- Error scenarios covered (404, 422, 409)
- Event publishing verified
- reset_state fixture used
```

---

### Step 5: Run Automated Validation Commands

**What to run:**

#### Type Checking
```bash
mypy src
```
**Must:** Pass with no errors
**Must:** All functions have type hints
**Configuration enforced:** `disallow_untyped_defs = true`

#### Linting
```bash
ruff check src
```
**Must:** Pass with no errors
**Configuration enforced:** 100 character line length, import sorting, PEP 8

#### Testing
```bash
pytest tests
```
**Must:** All tests pass
**Must:** 80%+ code coverage for new code

#### Test with coverage
```bash
pytest --cov=src tests
```

**Violations to flag:**
```
❌ mypy errors:
  src/activities/service.py:45: error: Argument 1 to "create_task" has incompatible type
  → Line-level feedback required
  
❌ ruff violations:
  src/activities/routes.py:50: E501 line too long (125 > 100 characters)
  → Line-level feedback required
  
❌ pytest failures:
  test_activities.py::TestActivitiesRoutes::test_create_task FAILED
  → Line-level feedback required
```

**Feedback template:**
```
✅ Validation passed
- mypy: 0 errors
- ruff: 0 errors
- pytest: 12 passed, 0 failed
- coverage: 87% (new code)
```

---

### Step 6: Apply Architecture Governance Checks

**What to check:**

#### A. Route → Service → Repository Layering
- [ ] Routes call services only (never repositories directly)
- [ ] Services call repositories only (never other services directly)
- [ ] Repositories have no business logic

**Check command:**
```bash
grep -r "from.*repository import" src/*/routes.py  # Should be empty
grep -r "from.*service import" src/*/repository.py  # Should be empty
```

#### B. No Cross-Module Repository Imports
- [ ] Activities repository only used in activities module
- [ ] Alerts repository only used in alerts module
- [ ] Staff repository only used in staff module
- [ ] Programmes repository only used in programmes module
- [ ] Reports repository only used in reports module (read-only)

**Violation example:**
```python
# ❌ FAIL: alerts/service.py importing from activities
from src.activities.repository import ActivitiesRepository

# ✅ PASS: alerts/service.py using EventBus
from src.shared.event_bus import EventBus
event_bus.subscribe(EventType.TASK_CREATED, self.handle_task_created)
```

#### C. EventBus Required for Side Effects
- [ ] Cross-module communication uses EventBus only
- [ ] No direct service-to-service calls between modules
- [ ] Side effect modules (alerts, reports) subscribe to events, not called directly

**Violation example:**
```python
# ❌ FAIL: Direct service call
class AlertsService:
    def __init__(self, activities_service: ActivitiesService):  # Forbidden!
        pass

# ✅ PASS: Event-based
class AlertsService:
    def __init__(self, event_bus: EventBus):
        event_bus.subscribe(EventType.TASK_CREATED, self.handle_task_created)
```

#### D. Reports Module Remains Read-Only
- [ ] Reports repository never modified (no create, update, delete)
- [ ] Reports service only reads data
- [ ] No events published from reports module
- [ ] Reports module never called from other services

**Check command:**
```bash
grep -n "await.*repository\." src/reports/service.py
# Should only show get_* and list_* calls, never create/update/delete
```

#### E. AppError Compliance
- [ ] All service exceptions are `AppError` or subclasses
- [ ] Never raw `Exception`, `ValueError`, `RuntimeError`
- [ ] All routes catch `AppError` and convert to `HTTPException`
- [ ] Error codes use `ErrorCode` enum

**Violation example:**
```python
# ❌ FAIL: Raw exception
raise ValueError("Task not found")

# ✅ PASS: AppError subclass
raise NotFoundError(resource_type="Task", resource_id=task_id)
```

#### F. No Business Logic in Routes
- [ ] No validation logic in route handlers
- [ ] No data transformation in routes
- [ ] No conditional logic in routes
- [ ] All business logic delegated to services

**Violation example:**
```python
# ❌ FAIL: Validation in routes
@router.post("/tasks")
async def create_task(task_create: TaskCreate, service=Depends(...)):
    if not task_create.title:
        raise HTTPException(status_code=422)
    return await service.create_task(task_create)

# ✅ PASS: Validation in service
@router.post("/tasks")
async def create_task(task_create: TaskCreate, service=Depends(...)):
    return await service.create_task(task_create)
```

**Governance Verdict:**
- ✅ PASS: All governance checks pass
- ❌ FAIL: Any governance violation present

**Governance Feedback Template:**
```
✅ Architecture Governance: PASS
- ✅ Route-Service-Repository layering correct
- ✅ No cross-module repository imports
- ✅ EventBus used for side effects
- ✅ Reports module read-only
- ✅ All errors are AppError subclasses
- ✅ No business logic in routes
```

---

### Step 7: Determine Verdict

**Based on all 6 previous steps, determine final verdict:**

#### PASS
All of:
- ✅ Step 1: Sprint contract complete
- ✅ Step 2: Summary clear and accurate
- ✅ Step 3: Code follows all patterns
- ✅ Step 4: Test coverage adequate (80%+)
- ✅ Step 5: All automated checks pass (mypy, ruff, pytest)
- ✅ Step 6: Architecture governance all green

#### CONDITIONAL_PASS
All of:
- ✅ Steps 1-6 complete BUT
- ⚠️ Minor issues found that don't fail gates (e.g., missing docstring, unused import)
- ⚠️ Remediation clear and low-risk

#### FAIL
Any of:
- ❌ Step 1: Contract incomplete or missing
- ❌ Step 2: Summary missing or unclear
- ❌ Step 3: Code pattern violations
- ❌ Step 4: Insufficient test coverage
- ❌ Step 5: Automated checks fail (mypy, ruff, pytest)
- ❌ Step 6: Architecture governance violations

**Final Verdict Template:**
```markdown
## Review Result

### Verdict: ✅ PASS

### Step 1: Sprint Contract
✅ Complete and clear

### Step 2: Summary
✅ Accurate, decisions documented

### Step 3: Source Code
✅ All patterns followed
✅ routes.py: Clean HTTP handling
✅ service.py: Business logic isolated
✅ repository.py: Data access only
✅ models.py: Well-organized

### Step 4: Test Coverage
✅ 87% coverage
✅ Integration tests present
✅ Error paths tested
✅ Events verified

### Step 5: Automated Validation
✅ mypy: 0 errors
✅ ruff: 0 errors
✅ pytest: 12 passed

### Step 6: Architecture Governance
✅ Layering correct
✅ No cross-module repo imports
✅ EventBus used correctly
✅ All errors are AppError
✅ No business logic in routes

### Overall Assessment
Code is production-ready and meets all StoreOps architecture standards.

### Remediation (if needed)
N/A - No issues found.
```

---

## Review Feedback Requirements

### File-Level Feedback
Provide feedback on each modified/created file:

```
### File: src/activities/routes.py
✅ All route handlers follow the dependency injection pattern
✅ All exceptions properly caught as AppError
📝 Line 45: Consider adding docstring to created_task function
```

### Line-Level Feedback (when violations found)
Provide specific line numbers and remediation:

```
### File: src/activities/service.py
Line 78: ❌ Raw exception used
  Current: raise ValueError("Invalid task status")
  Fix: raise BusinessRuleViolationError(message="Invalid task status")

Line 102: ❌ Missing type hint
  Current: async def process(self, data):
  Fix: async def process(self, data: dict[str, Any]) -> dict[str, Any]:
```

### Remediation Guidance
Always provide clear, actionable remediation:

```
### Issue: Missing event publishing
**Symptom:** Task created but no alert triggered
**Root Cause:** ActivitiesService.create_task() doesn't publish TASK_CREATED event
**Solution:**
  1. Add event_bus parameter to ActivitiesService.__init__
  2. Call await self.event_bus.publish(EventType.TASK_CREATED, {...})
  3. Add test to verify event published
**Impact:** Low - isolated to one method
```

---

## Quick Reference: Common Violations

### ❌ Route Layer Violations
- Direct repository import
- Business logic in route handler
- Manual error formatting instead of AppError
- Synchronous I/O operations

### ❌ Service Layer Violations
- Circular service imports
- Raw exceptions (ValueError, RuntimeError)
- Direct service-to-service calls (no EventBus)
- Missing event publishing for side effects

### ❌ Repository Layer Violations
- Service imports
- Business logic or validation
- Event publishing
- External API calls

### ❌ Architecture Violations
- Cross-module repository imports
- Reports module writing to another domain
- Missing EventBus usage
- Circular dependencies

### ❌ Code Quality Violations
- Missing type hints on any function
- Line length > 100 characters
- Raw exception usage
- Async function not awaited

---

## Review Checklist Summary

Use this checklist for quick reference:

```markdown
## Pre-Review
- [ ] Sprint contract exists and is clear
- [ ] generator-summary.md is present

## Code Review
- [ ] File organization and naming correct
- [ ] Route layer: HTTP only, Depends(), AppError
- [ ] Service layer: Business logic, validation, events
- [ ] Repository layer: Data access only, no business logic
- [ ] Models: Well-organized, type hints

## Test Review
- [ ] Integration tests for all CRUD operations
- [ ] Error path tests (404, 422, 409, 400)
- [ ] Event publishing verified
- [ ] reset_state fixture used

## Validation
- [ ] mypy passes
- [ ] ruff passes
- [ ] pytest passes
- [ ] Coverage >= 80%

## Governance
- [ ] Route-Service-Repository layering
- [ ] No cross-module repository imports
- [ ] EventBus used for side effects
- [ ] Reports read-only
- [ ] All errors are AppError subclasses
- [ ] No business logic in routes

## Final Decision
- [ ] PASS / CONDITIONAL_PASS / FAIL
```

---

**This skill encodes the complete code review process for StoreOps. Use it to achieve deterministic, consistent review results across all PRs and generated code.**
