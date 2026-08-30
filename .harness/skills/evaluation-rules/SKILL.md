# Evaluation Rules for StoreOps Generated Code

**Purpose:** Convert non-deterministic LLM output into deterministic PASS/FAIL decisions using weighted evaluation dimensions.

## Evaluation Framework

StoreOps code evaluation uses two independent dimensions, each with specific technical checks:

| Dimension | Weight | Purpose |
|-----------|--------|---------|
| **Architecture Compliance** | 50% | Validates clean architecture patterns |
| **Engineering Quality** | 50% | Validates code quality and testing |

**Final Score Formula:**
```
FINAL_SCORE = (Architecture_Score × 0.50) + (Engineering_Score × 0.50)
```

**Verdict Rules:**
- **PASS**: All hard fail gates pass AND score ≥ 90
- **CONDITIONAL_PASS**: All hard fail gates pass AND score 75-89
- **FAIL**: Any hard fail gate fails OR score < 75

---

## Dimension A: Architecture Compliance (50%)

**Weight:** 50% of final score  
**Purpose:** Ensure code follows StoreOps Route → Service → Repository architecture

### A1. Route-Service-Repository Layering (20% of Architecture)

**Check:** HTTP handlers do not directly call repositories

**Scoring:**
- ✅ 100%: All route handlers call services only, never repositories
- ⚠️  50%: Some route handlers call services, others call repositories directly
- ❌ 0%: Route handlers call repositories directly

**Implementation:**
```bash
# Check for direct repository imports in routes
grep -r "from.*repository import" src/*/routes.py

# Should return: (empty, no matches)
# If matches found: FAIL this dimension
```

**Example:**
```python
# ✅ PASS
@router.post("/tasks")
async def create_task(task_create: TaskCreate, service=Depends(get_activities_service)):
    return await service.create_task(task_create)

# ❌ FAIL
@router.post("/tasks")
async def create_task(task_create: TaskCreate, repo=Depends(get_activities_repository)):
    return await repo.create(task_create)
```

---

### A2. No Cross-Module Repository Imports (20% of Architecture)

**Check:** Repositories are only used within their own module

**Scoring:**
- ✅ 100%: Each repository only imported by its own module's service
- ⚠️  50%: One cross-module repository import found
- ❌ 0%: Multiple cross-module repository imports or circular imports

**Implementation:**
```bash
# Check activities repository imports
grep -r "from src.activities.repository import" src --exclude-dir=activities

# Check alerts repository imports  
grep -r "from src.alerts.repository import" src --exclude-dir=alerts

# Should return: (empty, no matches in other modules)
# If matches found: FAIL this dimension
```

**Example:**
```python
# ❌ FAIL: alerts/service.py importing activities repository
from src.activities.repository import ActivitiesRepository

# ✅ PASS: alerts/service.py subscribing to events from activities
from src.shared.event_bus import EventBus, EventType
event_bus.subscribe(EventType.TASK_CREATED, self.handle_task_created)
```

---

### A3. EventBus Required for Side Effects (20% of Architecture)

**Check:** Cross-module communication uses EventBus, not direct service calls

**Scoring:**
- ✅ 100%: All cross-module communication via EventBus (publish/subscribe)
- ⚠️  50%: Some cross-module communication via EventBus, some direct calls
- ❌ 0%: Direct service-to-service coupling between modules

**Implementation:**
```bash
# Check for direct service imports between modules (forbidden)
# alerts/service.py should NOT import ActivitiesService
grep -r "from src.activities.service import ActivitiesService" src/alerts
grep -r "from src.activities.service import ActivitiesService" src/programmes
grep -r "from src.activities.service import ActivitiesService" src/reports

# Should return: (empty, no matches)
# If matches found: FAIL this dimension
```

**Example:**
```python
# ❌ FAIL: Direct service-to-service coupling
class AlertsService:
    def __init__(self, activities_service: ActivitiesService):
        self.activities_service = activities_service
    
    async def check_task_overdue(self):
        tasks = await self.activities_service.list_tasks()  # Direct call!

# ✅ PASS: Event-based coupling
class AlertsService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.TASK_OVERDUE, self.handle_task_overdue)
    
    async def handle_task_overdue(self, payload: dict):
        # React to task being marked overdue
        pass
```

---

### A4. Reports Module Remains Read-Only (20% of Architecture)

**Check:** Reports module only reads data, never modifies it

**Scoring:**
- ✅ 100%: Reports repository only has get_* and list_* methods
- ⚠️  50%: Reports repository has one create/update/delete method
- ❌ 0%: Reports repository modifies data or writes to other domains

**Implementation:**
```bash
# Check reports/service.py for writes
grep -E "await self.repository\.(create|update|delete)" src/reports/service.py

# Should return: (empty, no matches)
# If matches found: FAIL this dimension

# Check for events published from reports (forbidden)
grep "await self.event_bus.publish" src/reports/service.py

# Should return: (empty, no matches)
```

**Example:**
```python
# ❌ FAIL: Reports writing data
class ReportsService:
    async def create_report(self, data):
        return await self.repository.create(data)  # Forbidden!

# ✅ PASS: Reports reading data only
class ReportsService:
    async def get_report(self, report_id: str):
        return await self.repository.get_by_id(report_id)
    
    async def list_reports(self):
        return await self.repository.list_all()
```

---

### A5. AppError Compliance (20% of Architecture)

**Check:** All errors in services are AppError or subclasses, never raw exceptions

**Scoring:**
- ✅ 100%: All service exceptions are AppError subclasses (ValidationError, NotFoundError, BusinessRuleViolationError, ConflictError)
- ⚠️  50%: One raw exception found (ValueError, RuntimeError, etc.)
- ❌ 0%: Multiple raw exceptions or critical error type violations

**Implementation:**
```bash
# Check for raw exception raises in services
grep -E "raise (ValueError|RuntimeError|Exception|TypeError|KeyError)" src/*/service.py

# Should return: (empty, no matches)
# If matches found: FAIL this dimension

# Check routes catch AppError (not bare except)
grep -A2 "except" src/*/routes.py | grep "except AppError"

# Should find AppError catches in all route handlers
```

**Error Hierarchy (must use these):**
```python
AppError (base)
  ├── ValidationError (422 - input validation failed)
  ├── NotFoundError (404 - resource not found)
  ├── BusinessRuleViolationError (400 - domain rule violated)
  └── ConflictError (409 - resource already exists)
```

**Example:**
```python
# ❌ FAIL: Raw exceptions
async def create_task(self, task_create: TaskCreate):
    if not task_create.title:
        raise ValueError("Title required")  # Raw exception!
    
    existing = await self.repository.get_by_email(task_create.email)
    if existing:
        raise RuntimeError("Already exists")  # Raw exception!

# ✅ PASS: AppError subclasses
async def create_task(self, task_create: TaskCreate):
    if not task_create.title:
        raise ValidationError(message="Title required")
    
    existing = await self.repository.get_by_email(task_create.email)
    if existing:
        raise ConflictError(
            resource_type="Task",
            message=f"Task with email {task_create.email} already exists"
        )
```

---

### A6. No Business Logic in Routes (20% of Architecture)

**Check:** Route handlers only handle HTTP, all logic delegated to services

**Scoring:**
- ✅ 100%: All routes are thin HTTP handlers calling services
- ⚠️  50%: Some routes have minor logic (data formatting)
- ❌ 0%: Routes contain validation, transformation, or decision logic

**Implementation:**
```bash
# Check route files for complex logic patterns
# Routes should only: receive request, call service, catch error, return response

# Violations to look for:
grep -E "(if |for |while |\.split|\.replace|\.format)" src/*/routes.py | grep -v "response_model" | grep -v "status_code"

# Complex logic in routes is suspicious
```

**Example:**
```python
# ❌ FAIL: Validation in routes
@router.post("/tasks")
async def create_task(task_create: TaskCreate, service=Depends(...)):
    if not task_create.title or len(task_create.title) < 3:
        raise HTTPException(status_code=422, detail="Title too short")
    
    return await service.create_task(task_create)

# ✅ PASS: Validation in service
@router.post("/tasks")
async def create_task(task_create: TaskCreate, service=Depends(...)):
    try:
        return await service.create_task(task_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

---

## Dimension B: Engineering Quality (50%)

**Weight:** 50% of final score  
**Purpose:** Ensure code quality, testing, and compliance with tooling standards

### B1. pytest Passes (25% of Engineering)

**Check:** All tests pass successfully

**Scoring:**
- ✅ 100%: All tests pass, 0 failures
- ⚠️  50%: 1-2 test failures, or timeout
- ❌ 0%: 3+ test failures

**Implementation:**
```bash
pytest tests

# Expected output:
# =================== test session starts ====================
# collected N items
# test_activities.py::...PASSED
# test_alerts.py::...PASSED
# ...
# =================== N passed in X.XXs ======================
```

**Common pytest failures:**
- Test assertion failures
- Fixture setup/teardown failures
- Async test not awaited (missing `@pytest.mark.asyncio`)
- reset_state fixture not used (causes test pollution)

---

### B2. mypy Passes (25% of Engineering)

**Check:** Type checking passes with strict mode

**Scoring:**
- ✅ 100%: mypy 0 errors with strict config
- ⚠️  50%: 1-2 type errors
- ❌ 0%: 3+ type errors or critical type safety issues

**Implementation:**
```bash
mypy src

# Expected output:
# Success: no issues found in X source files
```

**mypy Configuration (enforced in pyproject.toml):**
```toml
[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true          # All functions must have type hints
disallow_incomplete_defs = true       # Return types required
check_untyped_defs = true
no_implicit_optional = true
warn_no_return = true
warn_unreachable = true
```

**Common mypy violations:**
- Missing return type hint
- Missing parameter type hints
- Implicit Optional (parameter default None without Optional type hint)
- Any return type (function should specify actual type)

**Example:**
```python
# ❌ FAIL: mypy errors
async def create_task(task_create):  # Missing type hints!
    return await self.repository.create(task_create)

async def get_task(task_id: str):  # Missing return type!
    return await self.repository.get_by_id(task_id)

async def list_tasks(skip=0):  # Implicit Optional, should be skip: int = 0
    pass

# ✅ PASS: Full type hints
async def create_task(self, task_create: TaskCreate) -> Task:
    return await self.repository.create(task_create)

async def get_task(self, task_id: str) -> Task | None:
    return await self.repository.get_by_id(task_id)

async def list_tasks(self, skip: int = 0) -> tuple[list[Task], int]:
    return await self.repository.list_all(skip=skip)
```

---

### B3. ruff Passes (25% of Engineering)

**Check:** Linting passes with strict configuration

**Scoring:**
- ✅ 100%: ruff 0 errors/warnings
- ⚠️  50%: 1-3 linting issues
- ❌ 0%: 4+ linting issues or ignored rules

**Implementation:**
```bash
ruff check src

# Expected output:
# All checks passed! ✓
```

**ruff Configuration (enforced in pyproject.toml):**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "PIE", "PT", "RUF"]
# Enforces:
# E/W: PEP 8 errors/warnings
# F: Logical errors (Pyflakes)
# I: Import sorting (isort)
# N: PEP 8 naming
# UP: Modernize Python syntax
# B: Security/best practices (Bugbear)
# PT: Pytest best practices
```

**Common ruff violations:**
- Line too long (> 100 characters)
- Unused import
- Module level import not at top
- Naming convention violation (e.g., `taskID` instead of `task_id`)
- Dead code

**Example:**
```python
# ❌ FAIL: ruff violations
from src.activities.models import Task, TaskCreate, TaskStatus  # Too long line (>100 chars)
import os
from src.shared.errors import AppError  # Import not sorted

async def get_taskByID(task_id: str):  # Naming convention: should be get_task_by_id
    unused_var = 42  # Unused variable
    return await self.repository.get_by_id(task_id)

# ✅ PASS: ruff compliant
from src.activities.models import Task, TaskCreate, TaskStatus
from src.shared.errors import AppError
import os

async def get_task_by_id(task_id: str) -> Task | None:
    return await self.repository.get_by_id(task_id)
```

---

### B4. Business Rule Tests Exist (12.5% of Engineering)

**Check:** Tests cover business logic, not just happy path

**Scoring:**
- ✅ 100%: Multiple business rule tests (validation, constraints, constraints)
- ⚠️  50%: One business rule test
- ❌ 0%: No business rule tests (only happy path)

**Implementation:**
Look for test methods like:
- `test_*_validation_*` - Input validation tests
- `test_*_business_rule_*` - Domain constraint tests
- `test_*_error_*` - Error scenario tests

**Example Business Rule Tests:**
```python
class TestActivitiesService:
    async def test_create_task_validation_missing_title(self):
        """Test business rule: task title required."""
        task_data = {"status": TaskStatus.TODO}  # No title
        with pytest.raises(ValidationError):
            await self.service.create_task(task_data)

    async def test_create_task_validation_empty_title(self):
        """Test business rule: title cannot be whitespace."""
        task_data = {"title": "   ", "status": TaskStatus.TODO}
        with pytest.raises(ValidationError):
            await self.service.create_task(task_data)

    async def test_mark_complete_requires_date(self):
        """Test business rule: completed date required when marking done."""
        task = await self.service.create_task({...})
        with pytest.raises(BusinessRuleViolationError):
            await self.service.update_task(task.id, {"status": TaskStatus.DONE})
```

---

### B5. Acceptance Criteria Covered (12.5% of Engineering)

**Check:** Tests verify all acceptance criteria from sprint contract

**Scoring:**
- ✅ 100%: All acceptance criteria have corresponding tests
- ⚠️  50%: 75% of acceptance criteria covered
- ❌ 0%: < 50% of acceptance criteria covered

**Implementation:**
For each acceptance criterion in GIVEN/WHEN/THEN format, there should be a corresponding test:

```python
# Acceptance Criterion:
# GIVEN multiple tasks with different priorities
# WHEN listing tasks sorted by priority
# THEN tasks are returned in priority order (HIGH, MEDIUM, LOW)

# Corresponding test:
async def test_list_tasks_sorted_by_priority(self):
    """Test AC: Tasks sorted by priority."""
    # Create tasks with different priorities
    await self.service.create_task({
        "title": "Low", "priority": TaskPriority.LOW
    })
    await self.service.create_task({
        "title": "High", "priority": TaskPriority.HIGH
    })
    
    # List and verify order
    tasks, _ = await self.service.list_tasks(sort_by="priority")
    priorities = [t.priority for t in tasks]
    assert priorities == [TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
```

---

### B6. Code Quality (12.5% of Engineering)

**Check:** Code follows style, readability, and quality standards

**Scoring:**
- ✅ 100%: Clean code, good naming, docstrings present
- ⚠️  50%: Minor style issues, some missing docstrings
- ❌ 0%: Poor naming, no docstrings, hard-to-read code

**Standards:**
- ✅ Functions/classes have docstrings
- ✅ Docstrings follow format: `"""Short description. Args: ... Returns: ... Raises: ..."""`
- ✅ Variable names are descriptive (not `x`, `temp`, `data`)
- ✅ No dead code
- ✅ No magic numbers (use constants)
- ✅ Comments explain WHY, not WHAT

**Example:**
```python
# ❌ FAIL: Poor code quality
async def f(d):  # No docstring, poor naming
    x = d.get("title")
    if len(x) < 1:  # Magic number
        raise ValueError("bad")  # Poor error message
    self.r.create(d)  # Unclear abbreviations
    return self.r.get(d["id"])  # No event publishing

# ✅ PASS: Good code quality
async def create_task(self, task_create: TaskCreate) -> Task:
    """Create new task with validation.
    
    Args:
        task_create: Task creation data
    
    Returns:
        Created task
    
    Raises:
        ValidationError: If title is empty
    """
    # Validate required field
    if not task_create.title or not task_create.title.strip():
        raise ValidationError(message="Task title is required")
    
    # Persist and publish event
    task = await self.repository.create(task_create)
    await self.event_bus.publish(EventType.TASK_CREATED, {...})
    return task
```

---

## Hard Fail Conditions

**Any ONE of these causes INSTANT FAIL regardless of score:**

1. ❌ **pytest failure** - Any test fails
   ```bash
   pytest tests  # Must exit 0 (success)
   ```

2. ❌ **ruff failure** - Any linting error
   ```bash
   ruff check src  # Must have 0 errors
   ```

3. ❌ **mypy failure** - Any type error
   ```bash
   mypy src  # Must have 0 errors
   ```

4. ❌ **cross-module repository import** - Service in module A imports repository from module B
   ```python
   # In src/alerts/service.py:
   from src.activities.repository import ActivitiesRepository  # FAIL!
   ```

5. ❌ **missing EventBus requirement** - Cross-module communication without EventBus
   ```python
   # In src/alerts/service.py:
   class AlertsService:
       def __init__(self, activities_service: ActivitiesService):  # FAIL!
           pass
   ```

6. ❌ **reports module writes to another domain** - Reports creates/updates/deletes in another module's data
   ```python
   # In src/reports/service.py:
   await self.activities_repository.update(...)  # FAIL!
   ```

7. ❌ **raw Exception or RuntimeError** - Any service raises non-AppError exception
   ```python
   # In service.py:
   raise RuntimeError("Failed")  # FAIL!
   raise ValueError("Invalid")   # FAIL!
   raise Exception("Error")      # FAIL!
   ```

8. ❌ **acceptance criteria unimplemented** - Sprint contract criteria not satisfied
   ```
   Criterion: GIVEN task, WHEN status updated to DONE, THEN event published
   Result: No event published in code
   Verdict: FAIL!
   ```

9. ❌ **required tests missing** - Tests from sprint contract not implemented
   ```
   Required: test_create_task_missing_title
   Result: Test file has no such test
   Verdict: FAIL!
   ```

---

## Scoring Calculation

### Step 1: Calculate Architecture Compliance Score

```
A1 (Layering):                20 points × % (0, 50, or 100) = ___ / 20
A2 (No Cross-Module Imports): 20 points × % (0, 50, or 100) = ___ / 20
A3 (EventBus for Side Effects): 20 points × % (0, 50, or 100) = ___ / 20
A4 (Reports Read-Only):       20 points × % (0, 50, or 100) = ___ / 20
A5 (AppError Compliance):     20 points × % (0, 50, or 100) = ___ / 20
A6 (No Business Logic Routes):20 points × % (0, 50, or 100) = ___ / 20
                                        SUBTOTAL = ___ / 120

Architecture Score = (SUBTOTAL / 120) × 100 = ___% (0-100)
```

### Step 2: Calculate Engineering Quality Score

```
B1 (pytest Passes):           25 points × % (0, 50, or 100) = ___ / 25
B2 (mypy Passes):             25 points × % (0, 50, or 100) = ___ / 25
B3 (ruff Passes):             25 points × % (0, 50, or 100) = ___ / 25
B4 (Business Rule Tests):     12.5 points × % (0, 50, or 100) = ___ / 12.5
B5 (Acceptance Criteria):     12.5 points × % (0, 50, or 100) = ___ / 12.5
                                        SUBTOTAL = ___ / 100

Engineering Score = SUBTOTAL = ___% (0-100)
```

### Step 3: Calculate Final Score

```
Final Score = (Architecture_Score × 0.50) + (Engineering_Score × 0.50)
            = (___ × 0.50) + (___ × 0.50)
            = ___% (0-100)
```

### Step 4: Apply Hard Fail Conditions

```
IF any hard fail condition present:
  VERDICT = FAIL
ELIF Final Score >= 90 AND no hard fails:
  VERDICT = PASS
ELIF Final Score >= 75 AND no hard fails:
  VERDICT = CONDITIONAL_PASS
ELSE:
  VERDICT = FAIL
```

---

## Evaluation Report Template

```markdown
# StoreOps Code Evaluation Report

**Date:** 2026-08-29  
**Evaluator:** Claude Code Evaluator  
**Sprint:** ACTIVITIES-001  
**Code:** src/activities/  

---

## Hard Fail Conditions

✅ All hard fail gates pass:
- ✅ pytest: 12 passed
- ✅ mypy: 0 errors
- ✅ ruff: 0 errors
- ✅ No cross-module repository imports
- ✅ EventBus used for side effects
- ✅ Reports module unchanged
- ✅ All exceptions are AppError subclasses
- ✅ All acceptance criteria implemented
- ✅ All required tests present

---

## Dimension A: Architecture Compliance (50%)

| Check | Score | Evidence |
|-------|-------|----------|
| A1: Route-Service-Repository Layering | 100% | ✅ No repository imports in routes.py |
| A2: No Cross-Module Imports | 100% | ✅ activities/service.py imports only own repository |
| A3: EventBus for Side Effects | 100% | ✅ TASK_CREATED event published |
| A4: Reports Read-Only | N/A | Not modified in this sprint |
| A5: AppError Compliance | 100% | ✅ All exceptions are AppError subclasses |
| A6: No Business Logic in Routes | 100% | ✅ Validation in service only |

**Architecture Score: 100%**

---

## Dimension B: Engineering Quality (50%)

| Check | Score | Evidence |
|-------|-------|----------|
| B1: pytest Passes | 100% | ✅ 12 passed in 1.2s |
| B2: mypy Passes | 100% | ✅ Success: no issues found |
| B3: ruff Passes | 100% | ✅ All checks passed |
| B4: Business Rule Tests | 100% | ✅ 4 validation tests present |
| B5: Acceptance Criteria | 100% | ✅ 3/3 criteria covered |
| B6: Code Quality | 95% | ⚠️ 1 docstring missing on helper function |

**Engineering Score: 99%**

---

## Final Score Calculation

```
Architecture: 100% × 0.50 = 50 points
Engineering:  99% × 0.50  = 49.5 points
FINAL SCORE: 99.5% / 100
```

---

## Verdict

### ✅ PASS

**Rationale:**
- All hard fail gates pass
- Architecture score: 100% (all checks perfect)
- Engineering score: 99% (only minor docstring issue)
- Final score: 99.5% >= 90% threshold
- Code is production-ready

**Issues Found:**
- ⚠️ Minor: One helper function missing docstring (line 87 in service.py)
  ```python
  # Add docstring:
  async def _validate_task_dates(self, task: TaskCreate) -> None:
      """Validate task dates are in the future."""
      ...
  ```

**Remediation Priority:** Low - Does not block merge

---

## Next Steps

✅ Code is approved for merge  
✅ Ready for deployment  
✅ Meets all StoreOps architecture standards

---

**Evaluation Completed:** 2026-08-29 14:35:22  
**Evaluator Version:** 1.0.0
```

---

## Summary: Deterministic Evaluation

This framework provides **deterministic, reproducible evaluation** by:

1. ✅ **Eliminating ambiguity:** Each check has specific pass/fail criteria
2. ✅ **Preventing bias:** Hard fail conditions are non-negotiable
3. ✅ **Objective scoring:** Each dimension scored 0-100% based on evidence
4. ✅ **Measurable gates:** Automated tools (mypy, ruff, pytest) provide objective evidence
5. ✅ **Clear remediation:** Each failure has specific, actionable fix

**Same code + Same evaluator = Same verdict, every time.**

---

**Use this skill to convert subjective code review into objective, reproducible PASS/FAIL decisions.**
