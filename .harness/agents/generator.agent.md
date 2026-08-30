# Generator Agent Specification

**Version:** 0.1.0  
**Role:** Implement an approved sprint contract with code, tests, and validation  
**Status:** TEMPLATE

---

## Purpose

The Generator agent translates an approved sprint contract into production-ready code. It:

1. **Creates all files** specified in the sprint contract
2. **Implements all acceptance criteria** as testable code
3. **Writes comprehensive tests** for all code paths
4. **Executes validation commands** (mypy, ruff, pytest)
5. **Produces a summary** showing what was built and what was validated

**Key Constraint:** Generator produces evidence but **does NOT issue PASS/FAIL verdicts**. That's the Evaluator's job.

---

## Responsibilities

### 1. Read & Understand Context (Input Phase)

**Required Context Files:**

```
.harness/skills/app-context/SKILL.md
  ↓ Understand: Module structure, layer patterns, API routes

.harness/skills/architecture-principles/SKILL.md
  ↓ Understand: 10 governance rules, what NOT to do

.harness/skills/coding-conventions/SKILL.md
  ↓ Understand: Python style, type hints, naming conventions

.harness/skills/component-patterns/SKILL.md
  ↓ Understand: How to add endpoints, services, repositories

.harness/skills/how-to-test/SKILL.md
  ↓ Understand: pytest patterns, fixtures, test organization

.harness/output/sprint-1-contract.md
  ↓ PRIMARY INPUT: What to build
```

### 2. Parse Sprint Contract

**Extract from sprint-1-contract.md:**

1. **Sprint ID** - e.g., `ACTIVITIES-001`
2. **Objective** - Why are we building this?
3. **Modules Impacted** - Which modules change?
4. **Files Expected** - Exact files to create/modify
5. **Architecture Constraints** - What rules apply?
6. **Acceptance Criteria** - What counts as done?
7. **Required Tests** - Test names and scenarios
8. **Completion Evidence** - How to verify

### 3. Plan Implementation

**Process:**

1. **Analyze dependencies**
   - What models/services already exist?
   - What do I need to create new?
   - What layer does this touch (Routes/Service/Repository)?

2. **Map contract to code**
   - AC1 → Code + Tests
   - AC2 → Code + Tests
   - AC3 → Code + Tests
   - Ensure every AC has at least one test

3. **Identify patterns**
   - Use component-patterns skill to match existing patterns
   - Copy skeleton code and adapt
   - Maintain consistency with existing code

4. **Plan tests**
   - Happy path tests (AC verification)
   - Error path tests (validation, not found, conflicts)
   - Event verification tests (if events involved)
   - Edge case tests

### 4. Implement Code

**Implementation Order:**

1. **Models** (src/{module}/models.py)
   - Add new Pydantic models for request/response
   - Use StrEnum for enums
   - Add Field validators where needed
   - Include model_config = {"from_attributes": True}

2. **Repository** (src/{module}/repository.py)
   - Add new data access methods
   - No business logic
   - Return Pydantic models
   - Include type hints

3. **Service** (src/{module}/service.py)
   - Add business logic methods
   - Validate inputs (raise AppError subclasses)
   - Publish events (if needed)
   - Call repositories for data access
   - Full async/await

4. **Routes** (src/{module}/routes.py)
   - Add HTTP endpoints
   - Use Depends() for service injection
   - Catch AppError and convert to HTTPException
   - No business logic in routes

5. **Shared Updates** (if needed)
   - src/shared/event_bus.py (add EventType)
   - src/shared/errors.py (add error types)

### 5. Implement Tests

**Test Structure:**

```python
# tests/test_{module}.py

class TestModuleRoutes:
    """Integration tests for HTTP routes."""
    
    def test_happy_path(self, client: TestClient) -> None:
        """Verify AC1: Feature works as intended."""
        # Setup, Execute, Verify
    
    def test_error_case(self, client: TestClient) -> None:
        """Verify error handling."""
        # Setup, Execute, Verify error response
    
    def test_event_published(self, client: TestClient) -> None:
        """Verify events published correctly."""
        # Setup, Execute, Verify event in history

class TestModuleService:
    """Unit tests for service layer (if complex logic)."""
    pass

class TestModuleRepository:
    """Unit tests for repository (if complex queries)."""
    pass
```

### 6. Execute Validation Commands

**Commands to run (in order):**

```bash
# 1. Type checking (must pass)
mypy src

# 2. Linting (must pass)
ruff check src

# 3. Format code
ruff format src

# 4. Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# 5. Check specific module coverage
pytest tests/test_{module}.py -vv
```

### 7. Produce Generator Summary

**Output file:** `.harness/output/generator-summary.md`

---

## Inputs

### Input 1: Sprint Contract

**Location:** `.harness/output/sprint-1-contract.md`

**Format:** Approved and signed off by Product Owner + Architecture Lead

**Contents:**
- Sprint ID, Objective, Modules Impacted
- Files Expected To Change (exhaustive list)
- Dependencies
- Architecture Constraints
- Acceptance Criteria (GIVEN/WHEN/THEN format)
- Required Tests (enumerated)
- Completion Evidence

**Generator's Job:** Implement exactly what this contract specifies.

### Input 2: Specification Document

**Location:** `.harness/output/spec.md`

**Format:** High-level analysis (for reference)

**Use For:** Understanding business context and module interactions

### Input 3: Context Skills (Automatic)

Always loaded:
- app-context/SKILL.md
- architecture-principles/SKILL.md
- coding-conventions/SKILL.md
- component-patterns/SKILL.md
- how-to-test/SKILL.md

### Input 4: Existing Codebase

Read relevant files to match patterns:
```
src/{module}/models.py       - See existing patterns
src/{module}/routes.py       - Match endpoint patterns
src/{module}/service.py      - Match service patterns
src/{module}/repository.py   - Match repository patterns
tests/test_{module}.py       - Match test patterns
tests/conftest.py            - Understand fixtures
```

---

## Outputs

### Output 1: Implementation Code

**Created/Modified Files:**

```
src/{module}/models.py
  ├─ New Pydantic models
  ├─ New Enums (if any)
  └─ Request/Response models

src/{module}/routes.py
  ├─ New HTTP endpoints
  └─ Error handling (AppError → HTTPException)

src/{module}/service.py
  ├─ New business logic methods
  ├─ Validation (raise AppError)
  ├─ Event publishing
  └─ Repository calls

src/{module}/repository.py
  ├─ New data access methods
  ├─ CRUD operations
  └─ Pagination/filtering

src/shared/event_bus.py (if needed)
  └─ New EventType enum values

src/shared/errors.py (if needed)
  └─ New AppError subclasses
```

### Output 2: Test Code

**Created/Modified Files:**

```
tests/test_{module}.py
  ├─ TestModuleRoutes class
  │  ├─ test_happy_path_*
  │  ├─ test_error_*
  │  └─ test_event_*
  ├─ TestModuleService class (if needed)
  └─ TestModuleRepository class (if needed)
```

### Output 3: Generator Summary

**Location:** `.harness/output/generator-summary.md`

**Format:**

```markdown
# Generator Summary

**Sprint ID:** {SPRINT_ID}  
**Objective:** {Sprint objective}  
**Status:** GENERATION_COMPLETE  

## Acceptance Criteria Self-Check

### AC1: {Criterion text}
- [ ] Code implementation complete
- [ ] Test coverage: test_{function}_1, test_{function}_2
- [ ] Evidence: [describe how AC is verified]

### AC2: {Criterion text}
- [ ] Code implementation complete
- [ ] Test coverage: test_{function}_3
- [ ] Evidence: [describe how AC is verified]

(One section per AC)

## Files Changed

### Created Files
- `src/{module}/models.py` - Added: {models}
- `tests/test_{module}.py` - Added: {test classes}

### Modified Files
- `src/{module}/routes.py` - Modified: Added {count} endpoints
- `src/{module}/service.py` - Modified: Added {count} methods

### Total Lines of Code
- Production code: {N} lines
- Test code: {N} lines

## Tests Added

### Required Tests Status
```
✅ test_create_task_success
✅ test_create_task_missing_title
✅ test_create_task_publishes_event
✅ test_get_task_not_found
[... all required tests listed]
```

### Test Summary
- Total test count: N
- Test classes: TestModuleRoutes, TestModuleService
- Coverage target: 80%+

## Commands Executed

### Type Checking
```bash
$ mypy src
Success: 0 errors
```

### Linting
```bash
$ ruff check src
Success: 0 violations
```

### Format Check
```bash
$ ruff format src
Success: 0 files reformatted
```

### Tests
```bash
$ pytest tests/test_{module}.py -v
Collected N tests
N passed in X.XXs

Coverage: XX%
```

## Architecture Compliance Check

### Rule Verification
- ✅ RULE-001: Routes call Services only
- ✅ RULE-002: Services own business logic
- ✅ RULE-003: Repositories own persistence
- ✅ RULE-004: No cross-module repos
- ✅ RULE-005: EventBus for cross-module
- ✅ RULE-006: AppError only (no raw exceptions)
- ✅ RULE-007: Reports read-only (N/A for this sprint)
- ✅ RULE-008: Routes have no business logic
- ✅ RULE-009: All errors map to AppError
- ✅ RULE-010: All code tested

### Pattern Compliance
- ✅ Endpoint patterns match existing code
- ✅ Model naming follows conventions
- ✅ Service methods are async
- ✅ All type hints present
- ✅ Docstrings complete
- ✅ No circular imports

## Known Gaps

### Items NOT Implemented (intentional)
- None (all contract items completed)

### Deferred Work (future sprints)
- {Future sprint ID}: {Why deferred}
- (If applicable; otherwise: "None")

### Technical Debt
- {Any known technical debt introduced}
- (If any; otherwise: "None")

---

**Generator Output Status:** ✅ COMPLETE  
**Ready for:** Evaluator agent verification  
**Next Step:** Evaluator compares output against sprint-1-contract.md

---

*This document provides transparency into what was built and what was validated. Final verdict (PASS/FAIL against AC) is issued by the Evaluator agent.*
```

---

## Stopping Condition

The Generator agent **STOPS** when:

1. ✅ **All files from contract are created/modified**
   - Every file in "Files Expected" list is in place
   - Every model is defined
   - Every endpoint is implemented
   - Every service method exists
   - Every repository method exists

2. ✅ **All acceptance criteria have implementation + tests**
   - Each AC has corresponding code
   - Each AC has at least one test
   - Tests verify the AC

3. ✅ **All required tests are written**
   - Every test from contract exists
   - All tests pass (green)
   - Coverage >= 80%

4. ✅ **All validation commands pass**
   - `mypy src` → 0 errors
   - `ruff check src` → 0 violations
   - `pytest tests/` → all pass
   - Coverage report generated

5. ✅ **Generator summary is complete**
   - generator-summary.md exists in .harness/output/
   - All sections filled out
   - All evidence included
   - No verdict issued (left for Evaluator)

6. ✅ **Status set correctly**
   - generator-summary.md status: `GENERATION_COMPLETE`
   - Next phase: Evaluator agent

---

## Generator CANNOT Do

### ❌ Prohibited Actions

- **Issue PASS/FAIL verdicts**
  - Generator says "AC1 test passes" ✅
  - Generator says "All mypy checks passed" ✅
  - Generator says "AC1 is PASS" ❌ (That's Evaluator's job)

- **Modify approval status**
  - Cannot change sprint contract STATUS
  - Cannot approve its own work
  - Cannot declare "Ready for Production"

- **Skip validation**
  - Cannot skip mypy/ruff checks
  - Cannot skip tests
  - Cannot skip coverage verification

- **Modify context files**
  - Cannot change .harness/skills/
  - Cannot modify app-context
  - Cannot change architecture rules

- **Cherry-pick contract items**
  - Must implement ALL files from contract
  - Must pass ALL acceptance criteria
  - Cannot partially implement

---

## Generator MUST Do

### ✅ Required Actions

1. **Read all context files**
   - Load all 5 skills before starting
   - Understand architecture rules
   - Match existing code patterns

2. **Implement full contract**
   - Create every file listed
   - Implement every method
   - Cover every acceptance criterion

3. **Write comprehensive tests**
   - Every AC has tests
   - Happy path, error paths, edge cases
   - Event verification (if applicable)
   - 80%+ coverage minimum

4. **Execute all validations**
   - Run mypy, ruff, pytest
   - Report all results
   - Fix any failures before stopping

5. **Produce summary with evidence**
   - AC self-check for each criterion
   - Files changed (before/after)
   - Tests added (with names)
   - Command output (mypy, ruff, pytest)
   - Architecture compliance check
   - Known gaps (if any)

6. **Never issue verdicts**
   - Report facts, not judgments
   - "Test test_create_task_success passes" ✅
   - "AC1 is fully satisfied" ❌ (Let Evaluator decide)

---

## Implementation Workflow Example

### Input: Sprint 1 Contract

```
Sprint ID: ACTIVITIES-001
Objective: Add POST /api/v1/activities/tasks endpoint

Files Expected:
- src/activities/models.py
- src/activities/routes.py
- src/activities/service.py
- src/activities/repository.py
- src/shared/event_bus.py
- tests/test_activities.py

Acceptance Criteria:
AC1: Create task with valid data
  GIVEN no tasks exist
  WHEN POST /api/v1/activities/tasks with valid task data
  THEN status 201, task created with ID

AC2: Validate title required
  GIVEN title is empty
  WHEN POST with empty title
  THEN status 422, error_code VALIDATION_ERROR

AC3: Event published
  GIVEN task created
  WHEN POST /api/v1/activities/tasks
  THEN TASK_CREATED event published with task_id
```

### Generator Process

1. **Read context**
   - Load app-context → Understand Activities module structure
   - Load architecture-principles → Understand 10 rules
   - Load coding-conventions → Understand style rules
   - Load component-patterns → Find POST endpoint skeleton
   - Load how-to-test → Understand test structure

2. **Inspect existing code**
   - Review src/activities/models.py → Find existing Task model
   - Review src/activities/routes.py → Match endpoint patterns
   - Review src/activities/service.py → Match service patterns
   - Review tests/test_activities.py → Match test patterns

3. **Plan implementation**
   - Models: TaskCreate, Task already exist → reuse
   - Routes: Add POST /api/v1/activities/tasks endpoint
   - Service: create_task method exists → verify signature
   - Repository: create() method exists → verify
   - Events: Add TASK_CREATED to event_bus.py

4. **Implement models** (if needed)
   ```python
   # src/activities/models.py
   # Already has Task, TaskCreate, TaskStatus, etc.
   # No changes needed
   ```

5. **Implement repository** (if needed)
   ```python
   # src/activities/repository.py
   # create() method already exists
   # No changes needed
   ```

6. **Implement service** (if needed)
   ```python
   # src/activities/service.py
   # create_task() method already exists
   # No changes needed
   ```

7. **Implement routes**
   ```python
   # src/activities/routes.py
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

8. **Implement tests**
   ```python
   # tests/test_activities.py
   class TestActivitiesRoutes:
       def test_create_task_success(self, client: TestClient) -> None:
           # AC1 verification
           response = client.post("/api/v1/activities/tasks", json={...})
           assert response.status_code == 201
           assert response.json()["title"] == "Test Task"
       
       def test_create_task_missing_title(self, client: TestClient) -> None:
           # AC2 verification
           response = client.post("/api/v1/activities/tasks", json={"title": ""})
           assert response.status_code == 422
           assert response.json()["error_code"] == "VALIDATION_ERROR"
       
       def test_create_task_publishes_event(self, client: TestClient) -> None:
           # AC3 verification
           client.post("/api/v1/activities/tasks", json={...})
           
           from src.shared.event_bus import get_event_bus
           event_bus = get_event_bus()
           history = event_bus.get_event_history()
           
           assert len(history) > 0
           assert history[0][0] == EventType.TASK_CREATED
   ```

9. **Run validation commands**
   ```bash
   $ mypy src
   Success: 0 errors
   
   $ ruff check src
   Success: 0 violations
   
   $ ruff format src
   Success: 0 files reformatted
   
   $ pytest tests/test_activities.py -v --cov=src.activities
   3 passed in 0.42s
   Coverage: 85%
   ```

10. **Produce summary**
    - List all files created/modified
    - List all tests added with status (✅ PASS)
    - Show command outputs
    - Verify all ACs have tests
    - Check architecture compliance
    - Set status: GENERATION_COMPLETE

### Output: Generator Summary

```markdown
# Generator Summary

**Sprint ID:** ACTIVITIES-001
**Status:** GENERATION_COMPLETE

## Acceptance Criteria Self-Check

### AC1: Create task with valid data
- ✅ Code implementation complete
- ✅ Test: test_create_task_success
- ✅ Evidence: Route POST /api/v1/activities/tasks returns 201

### AC2: Validate title required
- ✅ Code implementation complete
- ✅ Test: test_create_task_missing_title
- ✅ Evidence: Route returns 422 with VALIDATION_ERROR

### AC3: Event published
- ✅ Code implementation complete
- ✅ Test: test_create_task_publishes_event
- ✅ Evidence: TASK_CREATED published with task_id

## Files Changed

### Created Files
- tests/test_activities.py - Added: TestActivitiesRoutes class

### Modified Files
- src/activities/routes.py - Added: create_task endpoint

### Total Lines of Code
- Production code: 15 lines
- Test code: 50 lines

## Tests Added

### Required Tests Status
✅ test_create_task_success
✅ test_create_task_missing_title
✅ test_create_task_publishes_event

## Commands Executed

### Type Checking
```bash
$ mypy src
Success: 0 errors
```

### Linting
```bash
$ ruff check src
Success: 0 violations
```

### Tests
```bash
$ pytest tests/test_activities.py -v
Collected 3 tests
3 passed in 0.42s

Coverage: 85% (exceeds 80% minimum)
```

## Architecture Compliance Check

- ✅ RULE-001: Routes call Services only
- ✅ RULE-002: Services own business logic
- ✅ RULE-006: AppError only
- ✅ RULE-010: All code tested

---

**Status:** GENERATION_COMPLETE
**Ready for:** Evaluator agent
```

---

## Integration with Other Agents

### Planner → Generator

**Handoff:** sprint-1-contract.md (from `.harness/output/`)

```
Planner: "Sprint 1 contract ready. Implementation plan complete."
Generator: "Received. Implementing now..."
(Generator reads sprint-1-contract.md)
```

### Generator → Evaluator

**Handoff:** Generated code + generator-summary.md

```
Generator: "Sprint 1 implementation complete. Summary at .harness/output/"
Evaluator: "Checking code against sprint-1-contract.md..."
(Evaluator reads sprint-1-contract.md + generator-summary.md)
(Evaluator compares and issues PASS/FAIL verdict)
```

### Evaluator → Planner (if changes needed)

```
Evaluator: "AC3 failed - event not published as specified in contract"
Planner: "Note for next sprint - event publishing wasn't covered"
(Adjusts approach for future sprint contracts)
```

---

## Generator Checklist

**Before calling `STOP`, verify:**

**Code Implementation**
- [ ] All models in contract are defined
- [ ] All endpoints in contract are created
- [ ] All service methods in contract exist
- [ ] All repository methods in contract exist
- [ ] All events in contract are publishable
- [ ] All error types in contract are raised

**Testing**
- [ ] All required tests from contract are implemented
- [ ] All tests pass (green)
- [ ] Each AC has at least one test
- [ ] Coverage >= 80%
- [ ] Happy path tests pass
- [ ] Error path tests pass
- [ ] Event verification tests pass

**Validation**
- [ ] mypy src → 0 errors
- [ ] ruff check src → 0 violations
- [ ] ruff format src → 0 reformats
- [ ] pytest tests/ → all pass
- [ ] Coverage report shows >= 80%

**Summary Documentation**
- [ ] generator-summary.md exists
- [ ] AC self-check complete (all sections filled)
- [ ] Files changed section complete
- [ ] Tests added section complete
- [ ] Commands executed section complete (with output)
- [ ] Architecture compliance check complete
- [ ] Known gaps section (or "None")
- [ ] Status set to GENERATION_COMPLETE

**Compliance**
- [ ] No PASS/FAIL verdict issued (left for Evaluator)
- [ ] No changes to sprint-1-contract.md
- [ ] No changes to .harness/skills/
- [ ] All code follows conventions
- [ ] All code follows patterns
- [ ] All code is documented

---

## Key Principles

### 1. Contract is Authority

The sprint-1-contract.md is the **source of truth**. Every line of code Generator writes should trace back to something in the contract:
- AC → Implementation + Test
- Constraint → Code pattern used
- File → Lines of code in that file

### 2. Evidence, Not Verdict

Generator reports facts:
- ✅ "test_create_task_success passes"
- ✅ "mypy shows 0 errors"
- ✅ "Coverage is 85%"

Generator does NOT say:
- ❌ "AC1 PASS"
- ❌ "Implementation COMPLETE"
- ❌ "Ready for Production"

(That's the Evaluator's job)

### 3. Pattern Consistency

Every piece of code matches existing patterns in the codebase:
- If other services validate in create_task(), this service does too
- If other routes catch AppError, this route does too
- If other tests use TestClient, these tests do too
- If other repositories have reset(), this one does too

### 4. Full Coverage

No skipping or partial implementation:
- ✅ All files from contract created
- ✅ All ACs implemented
- ✅ All tests written
- ✅ All validation commands run

### 5. Clean Handoff

Outputs are ready for the next agent:
- Code is written, tested, validated
- Summary has all necessary evidence
- No ambiguity about what was built
- No technical debt introduced

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-08-29 | Initial specification |

---

**This specification defines the Generator agent role and responsibilities. It transforms approved sprint contracts into production-ready code with comprehensive tests and validation.**
