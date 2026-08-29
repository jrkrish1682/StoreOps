# Sprint Decomposition for StoreOps Features

**Purpose:** Teach the Planner how to decompose StoreOps features into small, testable sprints that are appropriate for a single Generator/Evaluator cycle.

## Sprint Contract Structure

Every sprint must define these elements clearly and objectively:

### 1. Sprint ID

Unique identifier following pattern: `{MODULE}-{SEQUENCE}`

**Examples:**
- `ACTIVITIES-001` - First sprint in activities module
- `ACTIVITIES-002` - Second sprint in activities module
- `ALERTS-001` - First sprint in alerts module
- `STAFF-001` - First sprint in staff module
- `PROGRAMMES-001` - First sprint in programmes module
- `REPORTS-001` - First sprint in reports module

---

### 2. Objective

One-sentence, outcome-focused goal. Answers: "What user problem does this solve?"

**Format:** `Add/Modify/Implement [feature] to [achieve business outcome]`

**Good Examples:**
- ✅ `Add PATCH endpoint for bulk task status updates to allow store managers to quickly resolve multiple tasks`
- ✅ `Create task priority validation rules to prevent invalid priority values in the system`
- ✅ `Implement event publishing when tasks are marked overdue to trigger alert escalations`

**Bad Examples:**
- ❌ `Add PATCH endpoint` (no outcome stated)
- ❌ `Update activities module` (too vague)
- ❌ `Fix bugs` (not a specific feature)

---

### 3. Modules Impacted

List all modules that will change. StoreOps modules:
- `activities` - Task management
- `alerts` - Alert and escalation management
- `programmes` - Programme/initiative management
- `staff` - Staff/user management
- `reports` - Reporting and analytics (usually read-only)
- `shared` - Shared errors, event bus, dependencies

**Examples:**
- `Modules: activities` (self-contained feature)
- `Modules: activities, alerts` (activities creates tasks, alerts subscribes to events)
- `Modules: activities, alerts, shared` (if adding new EventType)

**Key Rule:**
- Most sprints touch only ONE module (best practice)
- Cross-module communication happens via EventBus events, not direct service calls
- Reports module almost never changes (read-only)

---

### 4. Files Expected To Change

List every file that will be created or modified. Use relative paths from `src/`.

**Pattern:**
```
src/{module}/models.py       - Add/modify Pydantic models
src/{module}/routes.py       - Add/modify HTTP endpoints
src/{module}/service.py      - Add/modify business logic
src/{module}/repository.py   - Add/modify data access
src/shared/errors.py         - Add new error types (if needed)
src/shared/event_bus.py      - Add new EventType (if needed)
tests/test_{module}.py       - Add tests
```

**Example (Complete):**
```
Files Expected:
- src/activities/models.py (modify: Add BulkUpdateRequest)
- src/activities/routes.py (modify: Add PATCH /tasks/{id} endpoint)
- src/activities/service.py (modify: Add update_task_bulk method)
- src/activities/repository.py (modify: Add update_bulk method)
- src/shared/event_bus.py (modify: Add TASK_STATUS_CHANGED event)
- tests/test_activities.py (add: bulk update tests)
```

**Example (Minimal):**
```
Files Expected:
- src/activities/service.py (modify: Add title validation)
- tests/test_activities.py (add: validation tests)
```

---

### 5. Dependencies

What must be done BEFORE this sprint? What blocks this sprint?

**Format:**
```
Dependencies:
- {Sprint ID}: {Reason}
- None (if independent)
```

**Examples:**
```
✅ ACTIVITIES-002 depends on ACTIVITIES-001
   Reason: Needs task creation endpoint from first sprint

✅ ALERTS-001 depends on ACTIVITIES-001
   Reason: Needs TASK_CREATED event published by activities

✅ STAFF-001 is independent
   Reason: No other modules needed yet
```

**Rule:** If sprint X publishes an event that sprint Y subscribes to, sprint X must complete first.

---

### 6. Architecture Constraints

Explicit list of "musts" and "must nots" for this sprint.

**Standard Constraints (always include):**
```
Architecture Constraints:
- Must follow Route → Service → Repository layering
- Must validate all inputs in Service, not routes
- Must use Pydantic models for request/response validation
- Must raise AppError subclasses, never raw exceptions
- Must use async/await for all I/O operations
```

**Feature-Specific Constraints (add as needed):**
```
✅ "Must publish TASK_CREATED event after task creation"
✅ "Must NOT call ActivitiesService from within AlertsService"
✅ "Must NOT modify reports module (read-only)"
✅ "Must validate task exists before updating"
✅ "Must return 404 if task not found"
✅ "Must include pagination support (skip, limit)"
✅ "Must NOT create direct repository imports in routes"
```

---

### 7. Acceptance Criteria

**Format:** GIVEN/WHEN/THEN (Gherkin-style)

Each criterion must be:
- ✅ Objectively testable (can write a test for it)
- ✅ Independently verifiable (can check it works)
- ✅ Specific (not vague)

**Template:**
```
GIVEN [initial state/precondition]
WHEN [user action/trigger]
THEN [observable result]
```

**Example 1: Create Task**
```
AC1: Create new task successfully
GIVEN no tasks exist in the system
WHEN POST /api/v1/activities/tasks with valid task data
THEN response status is 201 and task object is returned with ID

AC2: Validate task title required
GIVEN title field is empty
WHEN POST /api/v1/activities/tasks with empty title
THEN response status is 422 with error_code VALIDATION_ERROR

AC3: Event published on creation
GIVEN no subscribers yet
WHEN POST /api/v1/activities/tasks with valid data
THEN TASK_CREATED event is published with task ID in payload
```

**Example 2: Update Task Status (Bulk)**
```
AC1: Update single task status
GIVEN task exists with status TODO
WHEN PATCH /api/v1/activities/tasks/{id} with status=DONE
THEN response status is 200, task status changed to DONE

AC2: Verify task exists before update
GIVEN task with ID does not exist
WHEN PATCH /api/v1/activities/tasks/nonexistent with status=DONE
THEN response status is 404 with error_code NOT_FOUND

AC3: Event published on status change
GIVEN task with status TODO
WHEN PATCH endpoint updates status to DONE
THEN TASK_STATUS_CHANGED event published with task ID and new status
```

**Example 3: Validation Rule**
```
AC1: Reject invalid priority
GIVEN priority values are HIGH, MEDIUM, LOW
WHEN POST /api/v1/activities/tasks with priority=INVALID
THEN response status is 422 with error_code VALIDATION_ERROR

AC2: Accept valid priorities
GIVEN priority values are HIGH, MEDIUM, LOW
WHEN POST with each valid priority
THEN task created successfully with correct priority
```

---

### 8. Required Tests

List test cases that MUST exist for the sprint to be complete.

**Format:**
```
Required Tests:
- test_create_task_success
- test_create_task_missing_title
- test_create_task_publishes_event
- test_get_task_success
- test_get_task_not_found
- test_list_tasks_pagination
```

**Test Naming Convention:**
```
test_{function}_{scenario}
test_{function}_{condition}_{result}
```

**Mandatory Test Categories:**

1. **Happy Path** - Feature works as intended
   ```
   test_create_task_success
   test_update_task_success
   test_list_tasks_success
   ```

2. **Error Paths** - Error handling works
   ```
   test_create_task_validation_fails
   test_get_task_not_found
   test_update_nonexistent_task_returns_404
   ```

3. **Event Verification** - Events published correctly
   ```
   test_create_task_publishes_event
   test_update_task_publishes_event
   ```

4. **Edge Cases** - Boundary conditions
   ```
   test_create_task_with_long_title
   test_list_tasks_pagination_edge_cases
   test_empty_list_returns_zero_total
   ```

---

### 9. Completion Evidence

How will we verify the sprint is complete and working? What should be checked?

**Format:**
```
Completion Evidence:
- All acceptance criteria verified by tests
- All required tests pass
- Coverage >= 80% for new code
- mypy 0 errors
- ruff 0 errors
- Integration tests pass end-to-end
```

---

## Sprint Sizing Rules

**Goal:** Sprints should be small enough for one Generator/Evaluator cycle (1-2 hours of model time)

### Too Large (RED FLAG 🚩)
- ❌ Requires changes to 5+ files
- ❌ Requires changes to 3+ modules
- ❌ Requires 15+ test cases
- ❌ More than 3 acceptance criteria
- ❌ Complex orchestration across multiple services

**Example (Too large):**
```
"Refactor entire activities module to support real database"
→ Too many moving parts, unclear scope, multiple dependencies
```

### Just Right (GOOD 👍)
- ✅ Changes to 2-4 files
- ✅ Changes to 1 module (rarely 2)
- ✅ 5-10 test cases
- ✅ 2-4 acceptance criteria
- ✅ Self-contained feature

**Example (Just right):**
```
"Add PATCH endpoint for single task status update"
→ Clear scope, 3 files changed, 6 tests, 2 acceptance criteria
```

### Too Small (ORANGE FLAG ⚠️)
- ⚠️ Changes to 1 file only
- ⚠️ Single acceptance criterion
- ⚠️ 2-3 test cases only
- ⚠️ Trivial feature

**Example (Too small):**
```
"Fix typo in task model docstring"
→ Might not be worth a full sprint
```

---

## Complete Sprint Example

### PATCH /api/v1/activities/tasks/{id} Endpoint

**Sprint ID:** `ACTIVITIES-002`

**Objective:** Add PATCH endpoint for single task status updates to allow store managers to quickly update task status without full task replacement.

**Modules Impacted:** activities

**Files Expected To Change:**
```
- src/activities/models.py (add: TaskStatusUpdate model)
- src/activities/routes.py (add: PATCH /tasks/{id} endpoint)
- src/activities/service.py (add: update_task_status method)
- src/activities/repository.py (modify: add update method)
- src/shared/event_bus.py (add: TASK_STATUS_CHANGED event)
- tests/test_activities.py (add: 7 update tests)
```

**Dependencies:**
```
ACTIVITIES-001 must complete first
Reason: Needs existing tasks to update
```

**Architecture Constraints:**
```
- Must follow Route → Service → Repository layering
- Must validate new status is valid enum value (ValidationError if not)
- Must verify task exists before updating (NotFoundError if not)
- Must publish TASK_STATUS_CHANGED event after successful update
- Must use Pydantic model for request validation
- Must raise only AppError subclasses in service
- Must include task ID and new status in event payload
- Must NOT allow direct repository calls from routes
```

**Acceptance Criteria:**

```
AC1: Update task status successfully
GIVEN task exists with status TODO and priority HIGH
WHEN PATCH /api/v1/activities/tasks/{task_id} with {"status": "DONE"}
THEN response status is 200 and task.status is DONE and task.priority still HIGH

AC2: Validate status enum value
GIVEN only valid statuses are TODO, DONE, CANCELLED
WHEN PATCH with {"status": "INVALID_STATUS"}
THEN response status is 422 and error_code is VALIDATION_ERROR

AC3: Return 404 for nonexistent task
GIVEN task_id does not exist
WHEN PATCH /api/v1/activities/tasks/nonexistent with {"status": "DONE"}
THEN response status is 404 and error_code is NOT_FOUND

AC4: Publish event on successful update
GIVEN task with status TODO
WHEN PATCH updates status to DONE
THEN TASK_STATUS_CHANGED event published with task_id and new status DONE in payload

AC5: Preserve other task fields on update
GIVEN task has title, priority, description
WHEN PATCH updates only status
THEN all other fields remain unchanged (title, priority, description same)
```

**Required Tests:**
```
1. test_update_task_status_success
2. test_update_task_status_invalid_enum
3. test_update_task_status_nonexistent_task
4. test_update_task_status_publishes_event
5. test_update_task_status_preserves_other_fields
6. test_update_task_status_event_contains_payload
7. test_update_task_status_idempotent
```

**Completion Evidence:**
```
- All 5 acceptance criteria verified by integration tests
- All 7 required tests pass
- Coverage: 85% for activities module (new code)
- mypy: 0 errors in src/activities/
- ruff: 0 errors in src/activities/
- Event bus test confirms TASK_STATUS_CHANGED published
- Route integration test confirms endpoint returns 200, 404, 422 correctly
```

---

## Breakdown of Feature into Sprints

**Large Feature:** "Complete task management system"

**Decompose into sprints:**

```
ACTIVITIES-001: POST /api/v1/activities/tasks - Create task
├─ Files: models.py, routes.py, service.py, repository.py
├─ Tests: 5 (success, validation, event)
├─ AC: 3 (create, validate, event publish)
├─ Duration: 1 cycle

ACTIVITIES-002: GET /api/v1/activities/tasks/{id} - Get single task
├─ Files: routes.py, service.py (models reuse from 001)
├─ Tests: 3 (success, not found, response format)
├─ AC: 2 (get success, 404 handling)
├─ Duration: 0.5 cycle (simple)

ACTIVITIES-003: GET /api/v1/activities/tasks - List tasks
├─ Files: models.py (add list model), routes.py, service.py
├─ Tests: 5 (list, pagination, empty list, sort, filter)
├─ AC: 3 (list success, pagination works, returns total)
├─ Duration: 1 cycle

ACTIVITIES-004: PUT /api/v1/activities/tasks/{id} - Full update
├─ Files: routes.py, service.py, repository.py
├─ Tests: 6 (success, not found, validation, event, fields preserved)
├─ AC: 4 (update, validate, not found, event)
├─ Duration: 1 cycle

ACTIVITIES-005: PATCH /api/v1/activities/tasks/{id} - Partial update
├─ Files: models.py (add partial model), routes.py, service.py
├─ Tests: 5 (partial update, validation, not found, event, preserve)
├─ AC: 3 (partial update, validate, event)
├─ Duration: 1 cycle

ACTIVITIES-006: DELETE /api/v1/activities/tasks/{id} - Delete task
├─ Files: routes.py, service.py, repository.py
├─ Tests: 4 (delete success, not found, soft delete, event)
├─ AC: 2 (delete, 404 handling)
├─ Duration: 0.5 cycle

ACTIVITIES-007: GET /api/v1/activities/tasks?status=X - Filter by status
├─ Files: models.py (add status filter), routes.py, service.py
├─ Tests: 5 (filter by status, multiple statuses, empty result)
├─ AC: 2 (filter works, returns filtered list)
├─ Duration: 0.5 cycle

ACTIVITIES-008: Task validation rules
├─ Files: service.py (add validation methods)
├─ Tests: 8 (title required, priority enum, dates valid, etc)
├─ AC: 4 (validate title, priority, dates, reject invalid)
├─ Duration: 1 cycle

ACTIVITIES-009: Task assignment and owner tracking
├─ Files: models.py (add owner), routes.py, service.py, repository.py
├─ Tests: 6 (assign, list by owner, not found, validation)
├─ AC: 3 (assign task, list by owner, event publish)
├─ Duration: 1 cycle
```

**Total:** 9 sprints, each independent and self-contained

---

## Sprint Template (Copy/Paste)

Use this template when creating new sprints:

```markdown
## Sprint: {SPRINT_ID}

**Objective:** {What problem does this solve?}

**Modules Impacted:** {List modules}

**Files Expected To Change:**
```
- src/{module}/
- tests/test_{module}.py
```

**Dependencies:**
```
{List sprints that must complete first, or "None"}
```

**Architecture Constraints:**
```
- Must follow Route → Service → Repository layering
- Must validate inputs in Service, not routes
- Must use AppError subclasses only
- {Feature-specific constraints}
```

**Acceptance Criteria:**
```
AC1: {GIVEN} {WHEN} {THEN}
AC2: {GIVEN} {WHEN} {THEN}
AC3: {GIVEN} {WHEN} {THEN}
```

**Required Tests:**
```
- test_{function}_{scenario}
- test_{function}_{error_case}
- test_{function}_{event_verification}
```

**Completion Evidence:**
```
- All acceptance criteria verified
- All tests pass
- Coverage >= 80%
- mypy 0 errors
- ruff 0 errors
```
```

---

## Common Decomposition Patterns

### Pattern 1: CRUD Sprint Sequence
```
Sprint N.1: POST (Create)
Sprint N.2: GET (Read one)
Sprint N.3: GET (Read many/List)
Sprint N.4: PUT (Update full)
Sprint N.5: PATCH (Update partial) [optional]
Sprint N.6: DELETE (Delete)
```

### Pattern 2: Feature + Validation
```
Sprint N.1: Basic feature (happy path)
Sprint N.2: Validation rules
Sprint N.3: Error handling
Sprint N.4: Event integration
```

### Pattern 3: Single Module Expansion
```
Sprint N.1: Core resource management
Sprint N.2: Filtering/searching
Sprint N.3: Pagination
Sprint N.4: Sorting
Sprint N.5: Advanced queries
```

### Pattern 4: Cross-Module Integration
```
Sprint N.1: Module A feature (publishes event)
Sprint N.2: Module B subscribes to event
Sprint N.3: Module B reacts to event
Sprint N.4: Integration tests
```

---

## Sprint Decomposition Checklist

Before submitting a sprint contract, verify:

**Scope**
- [ ] Objective is one sentence
- [ ] Modules impacted are realistic (1-2 usually)
- [ ] Files expected are 2-5 files
- [ ] Not combining unrelated features

**Clarity**
- [ ] Sprint ID is unique and follows naming convention
- [ ] Objective answers "why" not just "what"
- [ ] Dependencies explicitly listed
- [ ] Architecture constraints are specific

**Testability**
- [ ] All acceptance criteria are GIVEN/WHEN/THEN format
- [ ] Each AC is objectively testable
- [ ] Required tests cover all AC
- [ ] Completion evidence is measurable

**Feasibility**
- [ ] Sprint fits in 1 Generator/Evaluator cycle
- [ ] No dependencies on incomplete work
- [ ] All constraints are achievable
- [ ] Tests are realistic

---

## Anti-Patterns: What NOT to Do

### ❌ Vague Objectives
```
WRONG: "Update activities"
RIGHT: "Add PATCH endpoint for status updates to allow managers to resolve multiple tasks quickly"
```

### ❌ Too Many Modules
```
WRONG: Modules: activities, alerts, programmes, staff, reports
RIGHT: Modules: activities (publish event), alerts (subscribe)
```

### ❌ Circular Dependencies
```
WRONG: 
  ACTIVITIES-002 depends on ALERTS-001
  ALERTS-001 depends on ACTIVITIES-002
RIGHT: ACTIVITIES-002 completes first, ALERTS-001 depends on it
```

### ❌ Vague Acceptance Criteria
```
WRONG: "System should handle updates correctly"
RIGHT: "GIVEN task exists, WHEN PATCH /tasks/{id} with new status, THEN status updated and event published"
```

### ❌ No Event Specification
```
WRONG: "Create task creation endpoint" (doesn't specify if event published)
RIGHT: "Create task endpoint and publish TASK_CREATED event with task ID"
```

### ❌ Testing Left to Chance
```
WRONG: "Add tests as needed"
RIGHT: "Required tests: test_create_task_success, test_create_task_validation, test_create_task_event"
```

---

## Tips for Good Sprint Decomposition

1. **One Feature Per Sprint**
   - ✅ "Add task creation endpoint"
   - ❌ "Add task CRUD and validation and events"

2. **Clear Success Definition**
   - ✅ Acceptance criteria are testable
   - ❌ "Make the system better"

3. **Realistic Scope**
   - ✅ 2-4 files modified
   - ❌ Refactor entire module

4. **Explicit Dependencies**
   - ✅ "Depends on ACTIVITIES-001"
   - ❌ "Maybe depends on other stuff"

5. **Event-Driven Communication**
   - ✅ "Publishes TASK_CREATED event"
   - ✅ "Alerts module subscribes to TASK_CREATED"
   - ❌ "Alerts calls ActivitiesService directly"

6. **Tests First Mindset**
   - Write acceptance criteria BEFORE code
   - Tests should be testable from the criteria
   - "Test will check..." = good criterion

---

**Use this skill to decompose large features into small, testable, independent sprints that are optimized for Generator/Evaluator cycles.**
