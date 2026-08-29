# StoreOps Architecture Principles & Governance Rules

**Version:** 0.1.0  
**Last Updated:** 2026-08-29  
**Scope:** Non-negotiable architecture governance for StoreOps

---

## Purpose

This skill encodes the **non-negotiable architecture governance rules** for StoreOps. Every rule has been validated against the existing codebase and must be enforced in all new contributions.

**Use this skill to:**
- Review pull requests for architectural compliance
- Design new modules/features
- Validate cross-module interactions
- Enforce layering boundaries
- Guide refactoring decisions

---

## RULE-001: Routes May Call Services Only

**Rule ID:** RULE-001  
**Category:** Layering / Dependency Boundaries

### Description

HTTP route handlers must **only** call Service layer methods. Routes **never** call repositories, access databases directly, or perform any business logic.

### Rationale

- **Separation of Concerns:** Routes handle HTTP protocol only
- **Business Logic Centralization:** All logic in Services ensures consistency
- **Testability:** Services can be unit tested independently of HTTP
- **Maintainability:** Single source of truth for business rules
- **Reusability:** Services can be called from multiple routes or async handlers

### Allowed Example ✅

**File:** `src/activities/routes.py`

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task_create: TaskCreate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Create new task - routes handles HTTP only."""
    try:
        # ✅ ALLOWED: Route calls service
        return await service.create_task(task_create=task_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Prohibited Example ❌

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(task_create: TaskCreate) -> Task:
    """❌ PROHIBITED: Route bypassing service layer."""
    # ❌ NEVER: Direct repository call
    repository = get_activities_repository()
    task = await repository.create(task_create)
    
    # ❌ NEVER: Business logic in route
    if not task.title:
        raise HTTPException(status_code=400, detail="Title required")
    
    return task
```

### Evaluation Method

- Static analysis: Check for imports of `Repository` classes in `routes.py` files
- Code review: Verify all repository access is indirect via services
- Testing: Can service be called without HTTP layer?

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Routes directly accessing repositories is an architectural violation.

---

## RULE-002: Services Own Business Logic

**Rule ID:** RULE-002  
**Category:** Responsibility / Single Responsibility Principle

### Description

All business logic, validation, orchestration, and domain rules belong **exclusively** in the Service layer. Services are the single source of truth for "how business rules are enforced."

### Rationale

- **Consistency:** Business rules applied uniformly across all access paths
- **Testability:** Business logic testable without HTTP or database layers
- **Centralization:** Changes to business logic happen in one place
- **Validation:** Input validation before any persistence
- **Orchestration:** Services coordinate across repositories and event bus

### Allowed Example ✅

**File:** `src/activities/service.py`

```python
class ActivitiesService:
    async def create_task(
        self,
        task_create: TaskCreate,
        current_user_id: str | None = None,
    ) -> Task:
        """Create task - business logic lives here."""
        
        # ✅ VALIDATION (business rule): Title required
        if not task_create.title or not task_create.title.strip():
            raise ValidationError(message="Task title is required")
        
        # ✅ PERSISTENCE: Via repository
        task = await self.repository.create(
            task_create=task_create,
            created_by=current_user_id,
        )
        
        # ✅ CROSS-MODULE SIDE EFFECT: Via EventBus
        await self.event_bus.publish(
            EventType.TASK_CREATED,
            {"task_id": task.id, "title": task.title},
        )
        
        return task
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Business logic in repository
class ActivitiesRepository:
    async def create(self, task_create: TaskCreate) -> Task:
        # ❌ NEVER: Validation in repository
        if not task_create.title:
            raise ValidationError(...)
        
        # ❌ NEVER: Publishing events from repository
        await self.event_bus.publish(...)
        
        return task

# ❌ PROHIBITED: Business logic in route
@router.post("/tasks")
async def create_task(task_create: TaskCreate) -> Task:
    # ❌ NEVER: Business logic in route handler
    if not task_create.title or not task_create.title.strip():
        raise HTTPException(...)
    return await get_repository().create(task_create)
```

### Evaluation Method

- Code review: Is validation in service, not routes/repositories?
- Tests: Can business logic be tested at service layer?
- Traceability: Can I find all enforcements of a business rule?

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Business logic scattered across layers creates inconsistency.

---

## RULE-003: Repositories Own Persistence Only

**Rule ID:** RULE-003  
**Category:** Responsibility / Data Access Layer

### Description

Repositories handle **only** CRUD operations, filtering, and pagination. Repositories **never** contain business logic, validation, or side effects.

### Rationale

- **Clarity:** Repository methods are simple, predictable data operations
- **Database Agnostic:** Easy migration from in-memory to SQLAlchemy to other ORMs
- **Composability:** Services can combine multiple repository calls safely
- **Testing:** Repositories testable without business context
- **No Side Effects:** Repositories don't trigger external actions

### Allowed Example ✅

**File:** `src/activities/repository.py`

```python
class ActivitiesRepository:
    """Repository owns persistence only."""
    
    async def create(self, task_create: TaskCreate, created_by: str | None = None) -> Task:
        """Create - pure data operation."""
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
    
    async def get_by_id(self, task_id: str) -> Task | None:
        """Get - pure read operation."""
        task_data = self._tasks.get(task_id)
        return Task.model_validate(task_data) if task_data else None
    
    async def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Task], int]:
        """Filter - pure query operation."""
        filtered = [t for t in self._tasks.values() if t["status"] == status]
        total = len(filtered)
        tasks = filtered[skip : skip + limit]
        return [Task.model_validate(t) for t in tasks], total
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Business logic in repository
class ActivitiesRepository:
    async def create(self, task_create: TaskCreate) -> Task:
        # ❌ NEVER: Validation
        if not task_create.title:
            raise ValidationError(...)
        
        # ❌ NEVER: Event publishing
        await self.event_bus.publish(EventType.TASK_CREATED, {...})
        
        # ❌ NEVER: Side effects
        send_email_notification(...)
        
        # ❌ NEVER: Orchestration
        other_repo = get_other_repository()
        await other_repo.update(...)
        
        task_data = {...}
        self._tasks[task_id] = task_data
        return Task.model_validate(task_data)
```

### Evaluation Method

- Code review: Does repository only call `self._data` operations?
- Grep: Search for `ValidationError`, `AppError`, `event_bus`, imports in repositories
- Import analysis: Repositories should only import models, not services or event_bus

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Repositories with side effects corrupt data layer.

---

## RULE-004: Cross-Module Repository Imports Prohibited

**Rule ID:** RULE-004  
**Category:** Module Boundaries / Circular Dependencies

### Description

A service in module A must **never** import and use a repository from module B. If data from another module is needed, the service must call that module's Service, not its Repository.

### Rationale

- **Circular Dependency Prevention:** Importing repositories creates implicit coupling
- **Abstraction:** Services are the public interface to a module's data
- **Business Rule Consistency:** Other modules' services know their own validation
- **Future Flexibility:** Easy to migrate repository implementation (in-memory → SQL)
- **Clear Boundaries:** Module-to-module only via Service → EventBus

### Allowed Example ✅

**File:** `src/alerts/service.py`

```python
class AlertsService:
    def __init__(
        self,
        repository: AlertsRepository,
        event_bus: EventBus,
        activities_service: ActivitiesService,  # ✅ ALLOWED: Service import
    ):
        self.repository = repository
        self.event_bus = event_bus
        self.activities_service = activities_service
    
    async def create_alert_for_task(self, task_id: str) -> Alert:
        """Create alert - uses other module's SERVICE, not REPOSITORY."""
        # ✅ ALLOWED: Call other module's service (read-only)
        task = await self.activities_service.get_task(task_id)
        
        # Use task data...
        alert = await self.repository.create(...)
        return alert
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Cross-module repository import
from src.activities.repository import get_activities_repository

class AlertsService:
    def __init__(self, repository: AlertsRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus
    
    async def create_alert_for_task(self, task_id: str) -> Alert:
        """❌ NEVER: Importing another module's repository."""
        # ❌ PROHIBITED: Direct repository access
        activities_repo = get_activities_repository()
        task = await activities_repo.get_by_id(task_id)
        
        alert = await self.repository.create(...)
        return alert
```

### Evaluation Method

- Import analysis: Scan all `service.py` files for `*.repository` imports
- AST parsing: Identify cross-module repository imports
- Code review: Is cross-module access via Service or Repository?

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Cross-module repository imports break abstraction.

---

## RULE-005: Cross-Module Side Effects Must Use EventBus

**Rule ID:** RULE-005  
**Category:** Cross-Module Communication / Event-Driven Architecture

### Description

When one module's service needs to trigger an action in another module (e.g., "create a task → trigger alert"), it must use the **EventBus**, never direct service calls. The triggering service publishes an event; interested services subscribe and react.

### Rationale

- **Loose Coupling:** Modules don't know about each other
- **Scalability:** New modules can subscribe to events without touching existing code
- **Testability:** Side effects can be verified by checking event history
- **Reusability:** One event can trigger multiple reactions
- **Observability:** All cross-module interactions visible in event history

### Allowed Example ✅

**File:** `src/activities/service.py`

```python
class ActivitiesService:
    async def create_task(self, task_create: TaskCreate) -> Task:
        """Create task and publish event for interested modules."""
        task = await self.repository.create(task_create)
        
        # ✅ ALLOWED: Publish event for other modules
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

**File:** `src/alerts/service.py` (Startup/Initialization)

```python
class AlertsService:
    def __init__(self, repository: AlertsRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus
        
        # ✅ ALLOWED: Subscribe to other module's events
        self.event_bus.subscribe(
            EventType.TASK_CREATED,
            self.handle_task_created,
        )
    
    async def handle_task_created(self, payload: dict) -> None:
        """React to task creation - no direct coupling to Activities."""
        task_id = payload["task_id"]
        priority = payload["priority"]
        
        if priority == "CRITICAL":
            await self.repository.create({
                "task_id": task_id,
                "message": "Critical task created",
            })
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Direct service call for side effects
class ActivitiesService:
    def __init__(
        self,
        repository: ActivitiesRepository,
        alerts_service: AlertsService,  # ❌ COUPLING
    ):
        self.repository = repository
        self.alerts_service = alerts_service  # ❌ Wrong!
    
    async def create_task(self, task_create: TaskCreate) -> Task:
        task = await self.repository.create(task_create)
        
        # ❌ PROHIBITED: Direct service call
        # This couples Activities and Alerts, making them inseparable
        if task.priority == "CRITICAL":
            await self.alerts_service.create_alert(task_id=task.id)
        
        return task
```

### Evaluation Method

- Code review: Do services import other services for side effects?
- Event history verification: Are cross-module side effects visible in event bus?
- Tests: Can alerts be tested independently of activities?
- Imports: Cross-module service imports in `__init__` are flags

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Direct service coupling breaks module isolation.

---

## RULE-006: Raw Exception or RuntimeError Prohibited in Routes and Services

**Rule ID:** RULE-006  
**Category:** Error Handling / Exception Policy

### Description

Routes and Services must **never** raise `Exception`, `RuntimeError`, `ValueError`, or other raw/built-in exceptions. All errors must be instances of `AppError` or its documented subclasses.

### Rationale

- **Consistency:** All errors have the same structure for clients
- **Error Semantics:** AppError codes communicate intent (validation vs. not-found vs. conflict)
- **HTTP Mapping:** AppError defines appropriate HTTP status codes
- **Testing:** Tests can assert on specific error types
- **Debugging:** Error codes and details provide context for logging

### Allowed Example ✅

**File:** `src/activities/service.py`

```python
class ActivitiesService:
    async def create_task(self, task_create: TaskCreate) -> Task:
        """Raise only AppError subclasses."""
        
        # ✅ ALLOWED: ValidationError (AppError subclass)
        if not task_create.title or not task_create.title.strip():
            raise ValidationError(message="Task title is required")
        
        task = await self.repository.create(task_create)
        return task
    
    async def get_task(self, task_id: str) -> Task:
        """Raise only AppError subclasses."""
        task = await self.repository.get_by_id(task_id)
        
        # ✅ ALLOWED: NotFoundError (AppError subclass)
        if not task:
            raise NotFoundError(resource_type="Task", resource_id=task_id)
        
        return task
    
    async def update_task(self, task_id: str, task_update: TaskUpdate) -> Task:
        """Raise only AppError subclasses."""
        task = await self.repository.get_by_id(task_id)
        
        # ✅ ALLOWED: BusinessRuleViolationError (AppError subclass)
        if task.status == TaskStatus.DONE and task_update.status == TaskStatus.IN_PROGRESS:
            raise BusinessRuleViolationError(
                message="Cannot move completed task back to in-progress",
                rule_name="TASK_STATE_TRANSITION"
            )
        
        return await self.repository.update(task_id, task_update)
```

### Prohibited Example ❌

```python
class ActivitiesService:
    async def create_task(self, task_create: TaskCreate) -> Task:
        """❌ PROHIBITED: Raising raw exceptions."""
        
        # ❌ NEVER: ValueError
        if not task_create.title:
            raise ValueError("Title is required")
        
        # ❌ NEVER: RuntimeError
        try:
            task = await self.repository.create(task_create)
        except Exception:
            raise RuntimeError("Failed to create task")
        
        # ❌ NEVER: Generic Exception
        if not task.id:
            raise Exception("Task ID missing")
        
        return task
```

### Evaluation Method

- AST Analysis: Search for `raise ValueError`, `raise RuntimeError`, `raise Exception` in routes/services
- Type Checking: Verify `except` clauses only catch `AppError`
- Code Review: Every error should be `AppError` or subclass
- Tests: Tests should assert on `AppError` subclasses

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Raw exceptions break error handling contract.

---

## RULE-007: Reports Module is Read-Only

**Rule ID:** RULE-007  
**Category:** Module Constraint / Data Integrity

### Description

The Reports module must **never** modify operational state. Reports service can **read** from other modules' repositories, but must **never** create, update, or delete operational data. Reports must **never** publish events.

### Rationale

- **Data Integrity:** Reporting cannot corrupt operational data
- **Safety:** Reports can be regenerated without side effects
- **Auditability:** Only operational services can change state
- **Read-Replica Pattern:** Reports act as a read-only analytics layer
- **Future Flexibility:** Reports can be cached/materialized safely

### Allowed Example ✅

**File:** `src/reports/service.py`

```python
class ReportsService:
    def __init__(
        self,
        repository: ReportsRepository,
        activities_repository: ActivitiesRepository,  # ✅ Read-only repo
    ):
        self.repository = repository
        self.activities_repository = activities_repository
    
    async def generate_activity_report(self, period_start, period_end) -> Report:
        """Generate report - read-only from other modules."""
        
        # ✅ ALLOWED: Read from repository
        activities, total = await self.activities_repository.list_all()
        
        # Process data...
        aggregated = self._aggregate_metrics(activities)
        
        # ✅ ALLOWED: Create report metadata (in reports repo only)
        report = await self.repository.create({
            "title": "Activity Report",
            "data": aggregated,
        })
        
        # ❌ DO NOT: Publish events
        # ❌ DO NOT: Modify activities
        
        return report
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Reports modifying state
class ReportsService:
    async def generate_activity_report(self, ...) -> Report:
        """❌ PROHIBITED: Report modifying operational state."""
        
        activities, total = await self.activities_repository.list_all()
        
        # ❌ NEVER: Modify activities
        for activity in activities:
            await self.activities_repository.update(activity.id, {...})
        
        # ❌ NEVER: Delete operational data
        await self.activities_repository.delete(activity.id)
        
        # ❌ NEVER: Publish events (side effects)
        await self.event_bus.publish(EventType.REPORT_GENERATED, {...})
        
        return report
```

### Evaluation Method

- Code review: Does reports service import/call write operations?
- Grep: Search for `repository.update()`, `repository.delete()`, `event_bus.publish()` in reports
- Impact analysis: Can reports be regenerated without changing operational data?
- Tests: Verify reports don't create test pollution

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Reports modifying state violates data integrity.

---

## RULE-008: Routes Must Not Contain Business Logic

**Rule ID:** RULE-008  
**Category:** Responsibility / Separation of Concerns

### Description

Route handlers are **only** HTTP protocol adapters. Routes must not:
- Validate business rules
- Perform calculations
- Orchestrate multiple steps
- Check preconditions beyond HTTP structure
- Transform data

### Rationale

- **Clarity:** Routes are "thin" adapters that translate HTTP to service calls
- **Testability:** Business logic tested via service tests, not HTTP tests
- **Reusability:** Business logic accessible from routes, async handlers, CLI, etc.
- **Maintainability:** Single place to change business rules (service)

### Allowed Example ✅

**File:** `src/activities/routes.py`

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task_create: TaskCreate,  # ✅ HTTP structural validation (Pydantic)
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Route only handles HTTP - service handles business logic."""
    try:
        # ✅ ONLY: Call service (business logic there)
        return await service.create_task(task_create=task_create)
    except AppError as e:
        # ✅ ONLY: Map AppError to HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,  # ✅ HTTP route parameter
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Route only retrieves - service provides business logic."""
    try:
        return await service.get_task(task_id=task_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Business logic in route
@router.post("/tasks")
async def create_task(task_create: TaskCreate) -> Task:
    """❌ PROHIBITED: Route contains business logic."""
    
    # ❌ NEVER: Input validation
    if not task_create.title or not task_create.title.strip():
        raise HTTPException(status_code=422, detail="Title required")
    
    # ❌ NEVER: Orchestration
    repository = get_activities_repository()
    task = await repository.create(task_create)
    
    # ❌ NEVER: Business rule checks
    if task.priority == "CRITICAL":
        event_bus = get_event_bus()
        await event_bus.publish(EventType.TASK_CREATED, {...})
    
    # ❌ NEVER: Data transformation
    return {"id": task.id, "name": task.title, "status": task.status.value}
```

### Evaluation Method

- Code review: Is route only calling one service method?
- Complexity metrics: Routes should be < 5 lines (except error handling)
- Logic depth: No nested if/loops in routes
- Imports: Routes should only import models, service, errors

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Business logic in routes creates inconsistency.

---

## RULE-009: All Externally Visible Failures Must Use AppError Hierarchy

**Rule ID:** RULE-009  
**Category:** Error Handling / API Contract

### Description

Any error visible to API clients (through HTTP responses) must be a properly mapped `AppError` with a valid HTTP status code and structured error response. Clients must never see stack traces, raw Python exceptions, or unstructured error messages.

### Rationale

- **API Contract:** Clients expect consistent error structure
- **Security:** Stack traces expose internal implementation details
- **Debugging:** Structured errors provide actionable information
- **Monitoring:** Error codes enable categorization and alerting
- **Usability:** Clients can parse and handle errors programmatically

### Allowed Example ✅

**File:** `src/activities/routes.py`

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task_create: TaskCreate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """All AppError translated to HTTPException."""
    try:
        return await service.create_task(task_create=task_create)
    except AppError as e:
        # ✅ ALLOWED: AppError → HTTPException → JSON response
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict(),  # Structured error response
        )

# Client sees:
# {
#   "error_code": "VALIDATION_ERROR",
#   "message": "Task title is required",
#   "details": {}
# }
```

**File:** `src/main.py`

```python
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    """Global handler for unhandled AppErrors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: Unhandled exceptions leak to client
@router.post("/tasks")
async def create_task(task_create: TaskCreate) -> Task:
    """❌ PROHIBITED: No error handling."""
    
    # ❌ NEVER: Raw exception escapes
    task = await get_activities_repository().create(task_create)
    
    # ❌ If exception here, client sees stack trace:
    # "Traceback (most recent call last):
    #   File 'routes.py', line X in create_task
    #     ...
    # KeyError: 'title'"

@router.post("/tasks")
async def create_task(task_create: TaskCreate) -> Task:
    """❌ PROHIBITED: Catching as generic Exception."""
    try:
        task = await service.create_task(task_create)
    except Exception as e:
        # ❌ NEVER: Return raw exception message
        raise HTTPException(
            status_code=500,
            detail=str(e),  # Unstructured, may expose internals
        )
```

### Evaluation Method

- Integration testing: All error responses are JSON with error_code, message, details
- Security scanning: No stack traces in HTTP responses
- Type checking: All caught exceptions are `AppError`
- Exception handler verification: Global handler for unhandled AppError

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Leaking stack traces is a security issue.

---

## RULE-010: All New Functionality Requires Automated Tests

**Rule ID:** RULE-010  
**Category:** Testing / Quality Assurance

### Description

Every new route, service method, or repository method must have automated tests. Tests must verify:
- **Happy path:** Normal operation succeeds
- **Error paths:** Errors raised correctly
- **Validation:** Invalid inputs rejected with correct errors
- **Events:** Published events have correct payload
- **State changes:** Data persisted correctly

### Rationale

- **Confidence:** Automated tests catch regressions quickly
- **Documentation:** Tests show how to use the code
- **Maintainability:** Safe to refactor with test coverage
- **Quality:** Enforced by CI/CD pipeline
- **Coverage:** Minimum 80% code coverage enforced

### Allowed Example ✅

**File:** `tests/test_activities.py`

```python
class TestActivitiesRoutes:
    """Tests for activities routes."""
    
    def test_create_task_success(self, client: TestClient) -> None:
        """Happy path: Task creation succeeds."""
        task_data = {
            "title": "Test Task",
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        response = client.post("/api/v1/activities/tasks", json=task_data)
        
        # ✅ Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert "id" in data
    
    def test_create_task_missing_title(self, client: TestClient) -> None:
        """Error path: Missing title rejected."""
        task_data = {
            "title": "",  # Empty title
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        response = client.post("/api/v1/activities/tasks", json=task_data)
        
        # ✅ Verify error response
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_create_task_publishes_event(self, client: TestClient) -> None:
        """Event: TASK_CREATED published on creation."""
        task_data = {
            "title": "Test Task",
            "priority": TaskPriority.HIGH,
            "category": TaskCategory.OPERATIONAL,
        }
        client.post("/api/v1/activities/tasks", json=task_data)
        
        # ✅ Verify event published
        from src.shared.event_bus import get_event_bus
        event_bus = get_event_bus()
        history = event_bus.get_event_history()
        
        assert len(history) == 1
        assert history[0][0] == EventType.TASK_CREATED
        assert history[0][1]["title"] == "Test Task"
    
    def test_get_task_not_found(self, client: TestClient) -> None:
        """Error path: Nonexistent task returns 404."""
        response = client.get("/api/v1/activities/tasks/nonexistent")
        
        # ✅ Verify 404 response
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "NOT_FOUND"
```

### Prohibited Example ❌

```python
# ❌ PROHIBITED: No tests for new feature
@router.post("/tasks/bulk")
async def create_tasks_bulk(
    tasks: list[TaskCreate],
    service: ActivitiesService = Depends(get_activities_service),
):
    """New bulk creation endpoint - ❌ NO TESTS."""
    # ❌ NEVER: Ship code without tests
    created = []
    for task in tasks:
        created.append(await service.create_task(task))
    return created

# ❌ PROHIBITED: Incomplete test coverage
class TestActivities:
    def test_create_task(self, client: TestClient):
        """Incomplete: Only happy path tested."""
        response = client.post("/api/v1/activities/tasks", json={...})
        assert response.status_code == 201
        
        # ❌ NEVER: Missing error path tests
        # ❌ NEVER: Missing event verification
        # ❌ NEVER: Missing validation tests
```

### Evaluation Method

- CI/CD enforcement: Pull requests blocked without tests
- Coverage report: Minimum 80% code coverage
- Test naming: Tests describe what they verify
- Test organization: Class-based organization by concern
- Fixture usage: Using `reset_state` fixture

### HARD FAIL? **YES** 🚫

**Violation Severity:** Critical - Untested code is a liability.

---

## Summary: Rule Enforcement Strategy

| Rule | Category | Hard Fail | Verification |
|------|----------|-----------|--------------|
| RULE-001 | Layering | ✅ YES | Import analysis, code review |
| RULE-002 | Responsibility | ✅ YES | Code review, test verification |
| RULE-003 | Responsibility | ✅ YES | Code review, static analysis |
| RULE-004 | Boundaries | ✅ YES | Import analysis, AST parsing |
| RULE-005 | Communication | ✅ YES | Code review, event verification |
| RULE-006 | Errors | ✅ YES | AST analysis, exception handling |
| RULE-007 | Constraints | ✅ YES | Code review, state mutation detection |
| RULE-008 | Responsibility | ✅ YES | Code review, complexity metrics |
| RULE-009 | Errors | ✅ YES | Integration tests, security scan |
| RULE-010 | Testing | ✅ YES | Coverage reports, CI/CD |

---

## When to Use This Skill

Use this skill to:

### 🔍 Code Review
- Check PR for violations of the 10 rules
- Reference specific rule when requesting changes
- Link to examples from codebase

### 🏗️ Architecture Design
- Design new modules/features following these rules
- Verify cross-module interactions don't violate boundaries
- Plan EventBus subscriptions for cross-module side effects

### 🧪 Testing
- Ensure new tests verify happy path, error paths, events
- Check minimum 80% coverage
- Reference test patterns from existing modules

### 🐛 Debugging
- Trace violations when features don't work
- Use rules to identify design issues
- Plan refactoring to restore compliance

### 📚 Onboarding
- Teach new contributors architecture constraints
- Reference real examples from codebase
- Set expectations for pull request reviews

---

## Escalation Path

**When a rule is violated:**

1. **Review:** Identify which rule(s) are violated
2. **Communicate:** Reference specific rule and example
3. **Fix:** Guide contributor to compliant pattern
4. **Verify:** Re-review until compliant
5. **Block:** CI/CD gates enforcement of hard-fail rules

**All 10 rules are HARD FAIL:** Violations must be fixed before merge.

---

*For application context and module details, see [[app-context]]. For testing patterns, see [[how-to-test]]. For code style, see [[coding-conventions]].*
