# Sprint Contract: ACTIVITIES-003

**Sprint ID:** `ACTIVITIES-003`  
**Title:** Shift Handover Bulk Activity Status Update  
**Objective:** Enable store managers to complete multiple pending activities in one request during shift handovers with transparent per-activity success/failure reporting and audit logging

---

## Sprint Identity

**Sprint ID:** `ACTIVITIES-003`  
**Title:** Shift Handover Bulk Activity Status Update  
**Objective:** Add PATCH `/api/v1/activities/bulk-status` endpoint to allow bulk status updates during shift handovers with partial failure support and audit logging

**Feature Scope:** Bulk update 1-100 activities to new status; return item-level success/failure breakdown

---

## Scope Definition

### Modules Impacted

| Module | Impact | Reason |
|--------|--------|--------|
| **activities** | Core change | Add endpoint, service method, repository method, models |
| **shared** | Minimal | Error handling via existing AppError hierarchy |

### Files Expected To Change

```
Created Files:
  (None - all changes to existing modules)

Modified Files:
  src/activities/models.py
    - Add BulkActivityStatusUpdate request model
    - Add BulkActivityStatusUpdateResult response model
    - Add BulkUpdateFailedItem (per-item failure)
    - Add BulkUpdateSummary (summary counts)
  
  src/activities/routes.py
    - Add PATCH /bulk-status endpoint
  
  src/activities/service.py
    - Add bulk_update_activities(activity_ids, new_status) async method
    - Coordinate validation, repository calls, event publishing, error handling
  
  src/activities/repository.py
    - Add bulk_update_status(activity_ids, new_status) async method
  
  tests/test_activities.py
    - Add TestActivitiesBulkUpdate test class with 10+ test methods
```

---

## Dependencies

### Prerequisites

**None.** This sprint is independent.

- No dependent sprints required
- No other modules' events required
- Does not block other sprints

### Blocked By

- None

---

## Architecture Contract

### Constraints (Non-Negotiable)

**Standard Constraints (All Sprints):**
```
✅ Must follow Route → Service → Repository layering
✅ Must validate all inputs in Service layer, not routes
✅ Must raise only AppError subclasses, never raw exceptions
✅ Must use async/await for all I/O operations
✅ Must use Pydantic models for request/response validation
```

**Feature-Specific Constraints:**
```
✅ Must process all activities (none skipped due to error)
✅ Must create activity log entry per successfully updated activity
✅ Must publish TASK_STATUS_CHANGED event per successfully updated activity
✅ Must NOT update activity if request-level validation fails (all-or-nothing at request level)
✅ Must accept 1-100 activity IDs (reject if empty or > 100)
✅ Must return HTTP 200 for partial/full success (never 404 or 400 once validation passes)
✅ Must include detailed error info (activity_id, error_code, message) for each failed activity
✅ Must NOT call other services (only repository + event_bus)
✅ Must validate status value against TaskStatus enum before processing
✅ Must support shift handover audit context (tag logs with "shift_handover")
```

### Rules Enforcement

| Rule | Enforcement | Implementation |
|------|-------------|-----------------|
| **RULE-001: Routes call services only** | ✅ Routes → Service | Route calls `service.bulk_update_activities()` only |
| **RULE-002: Services own business logic** | ✅ Business logic in service | Service validates, coordinates, publishes events |
| **RULE-003: Repositories own persistence** | ✅ Repository isolation | Repository has `bulk_update_status()` method only |
| **RULE-004: No cross-module repo imports** | ✅ Single module | Only activities module touched |
| **RULE-005: EventBus for cross-module comms** | ✅ Via EventBus | Publishes `TASK_STATUS_CHANGED` events |
| **RULE-006: AppError exceptions only** | ✅ AppError hierarchy | All errors wrapped in AppError subclasses |
| **RULE-007: Reports read-only** | ✅ N/A | Reports module not involved |
| **RULE-008: Routes no business logic** | ✅ Routes thin | Routes only call service, format response |
| **RULE-009: All exceptions map to AppError** | ✅ HTTPException wrapping | Routes catch AppError → HTTPException |
| **RULE-010: All code tested** | ✅ 80%+ coverage | All paths, AC, errors tested |

---

## Acceptance Criteria (ALL GIVEN/WHEN/THEN FORMAT)

### AC1: Complete All Activities Successfully (Full Success)

```
GIVEN three activities exist in repository
  AND activity-1 (Restock dairy) has status TODO
  AND activity-2 (Floor check) has status IN_PROGRESS
  AND activity-3 (Compliance review) has status TODO
  AND current_user is authenticated as manager
WHEN PATCH /api/v1/activities/bulk-status
  WITH headers: { "Authorization": "Bearer <token>" }
  WITH body: { "activity_ids": ["activity-1", "activity-2", "activity-3"], "new_status": "DONE" }
THEN HTTP response status is 200 (NOT 201, NOT 204)
  AND response.succeeded is array with exactly 3 items
  AND response.succeeded[0] has id="activity-1", status="DONE", updated_at=[timestamp]
  AND response.succeeded[1] has id="activity-2", status="DONE", updated_at=[timestamp]
  AND response.succeeded[2] has id="activity-3", status="DONE", updated_at=[timestamp]
  AND response.failed is empty array (zero items)
  AND response.summary.total = 3
  AND response.summary.succeeded = 3
  AND response.summary.failed = 0
  AND EventBus publishes TASK_STATUS_CHANGED event exactly 3 times (one per activity)
  AND Each event payload contains: { activity_id, old_status, new_status, updated_at, updated_by }
  AND Repository activity_log table has exactly 3 new entries
  AND Each audit entry has: activity_id, action="status_changed", details={old_status, new_status, bulk_update=true, context="shift_handover"}
  AND Activity repository reflects all 3 activities with status="DONE"
```

### AC2: Partial Success - Mixed Outcomes (Deterministic Per-Activity Handling)

```
GIVEN activity-1 (Restock dairy) exists with status TODO
  AND activity-2 (Floor check) exists with status DONE
  AND activity-99 does NOT exist
  AND current_user is authenticated as manager
WHEN PATCH /api/v1/activities/bulk-status
  WITH body: { "activity_ids": ["activity-1", "activity-2", "activity-99"], "new_status": "BLOCKED" }
THEN HTTP response status is 200 (ALWAYS 200 for partial success, never 404)
  AND response.succeeded is array with exactly 1 item
  AND response.succeeded[0] has id="activity-1", status="BLOCKED", updated_at=[timestamp]
  AND response.failed is array with exactly 2 items
  AND response.failed contains entry: { activity_id: "activity-2", error_code: "BUSINESS_RULE_VIOLATION", message: contains "Cannot transition" }
  AND response.failed contains entry: { activity_id: "activity-99", error_code: "NOT_FOUND", message: contains "does not exist" }
  AND response.summary.total = 3
  AND response.summary.succeeded = 1
  AND response.summary.failed = 2
  AND activity-1 in repository has status DONE → BLOCKED (successfully updated)
  AND activity-2 in repository STILL has status DONE (not updated)
  AND activity-99 remains nonexistent
  AND EventBus publishes TASK_STATUS_CHANGED event exactly 1 time (only for activity-1)
  AND Activity log has exactly 1 new entry (only for activity-1)
  AND Activity log entry for activity-1 has action="status_changed", old_status="TODO", new_status="BLOCKED", context="shift_handover"
```

### AC3: Validation Failure - Empty Activity List (Request-Level Validation)

```
GIVEN activity-1 exists with status TODO
WHEN PATCH /api/v1/activities/bulk-status
  WITH body: { "activity_ids": [], "new_status": "DONE" }
THEN HTTP response status is 400 (Bad Request)
  AND response.error_code = "VALIDATION_ERROR"
  AND response.message contains "activity_ids" AND contains "empty" or "required"
  AND response.details.field = "activity_ids"
  AND NO HTTP 200 response (validation fails before processing)
  AND activity-1 in repository STILL has status TODO (not modified)
  AND EventBus publishes ZERO events (no processing occurred)
  AND Activity log has ZERO new entries
```

### AC4: Validation Failure - Invalid Status Enum (Request-Level Validation)

```
GIVEN activity-1 exists with status TODO
WHEN PATCH /api/v1/activities/bulk-status
  WITH body: { "activity_ids": ["activity-1"], "new_status": "INVALID_STATUS" }
THEN HTTP response status is 422 (Unprocessable Entity)
  AND response.error_code = "VALIDATION_ERROR"
  AND response.message contains "new_status" AND contains "valid" or "enum" or "INVALID_STATUS"
  AND response.details.field = "new_status"
  AND NO HTTP 200 response
  AND activity-1 in repository STILL has status TODO (not modified)
  AND EventBus publishes ZERO events
  AND Activity log has ZERO new entries
```

### AC5: Validation Failure - Too Many Activities (Request-Level Validation)

```
GIVEN 101 activity IDs exist in database
WHEN PATCH /api/v1/activities/bulk-status
  WITH body: { "activity_ids": [101 unique activity IDs], "new_status": "DONE" }
THEN HTTP response status is 400 (Bad Request)
  AND response.error_code = "VALIDATION_ERROR"
  AND response.message contains "activity_ids" AND contains "maximum" AND contains "100"
  AND response.details.field = "activity_ids"
  AND NO HTTP 200 response
  AND NO activities in repository are modified (all remain unchanged)
  AND EventBus publishes ZERO events
  AND Activity log has ZERO new entries
```

---

## Test Contract

### AC → Test Mapping (EXPLICIT)

| Acceptance Criterion | Primary Test | Secondary Tests | Coverage |
|------|---------|---------|----------|
| **AC1: Full Success** | `test_bulk_update_all_succeed` | `test_bulk_update_single_activity`, `test_bulk_update_response_format` | 3 activities succeed, events published, audit entries created |
| **AC2: Partial Success** | `test_bulk_update_partial_success` | `test_bulk_update_activity_not_found`, `test_bulk_update_business_rule_violation` | Mixed success/failure, per-activity error reporting |
| **AC3: Empty List** | `test_bulk_update_empty_activity_list` | N/A | HTTP 400, error_code=VALIDATION_ERROR |
| **AC4: Invalid Status** | `test_bulk_update_invalid_status_enum` | N/A | HTTP 422, error_code=VALIDATION_ERROR |
| **AC5: Too Many Activities** | `test_bulk_update_too_many_activities` | N/A | HTTP 400, error_code=VALIDATION_ERROR |

**Coverage Guarantee:** Every AC has ≥1 test; every test verifies deterministic behavior

### Required Tests

All tests go in `tests/test_activities.py` under class `TestActivitiesBulkUpdate`

```
✅ test_bulk_update_all_succeed [AC1]
   Setup: Create 3 activities with status TODO, IN_PROGRESS, TODO
   Action: PATCH /api/v1/activities/bulk-status with all 3 activity_ids, new_status=DONE
   Verify HTTP: 200 status code
   Verify Response: response.succeeded has 3 items, response.failed is empty
   Verify Repository: all 3 activities have status=DONE in database
   Verify EventBus: exactly 3 TASK_STATUS_CHANGED events published
   Verify AuditLog: exactly 3 activity log entries created with action="status_changed", context="shift_handover"
   Verify Summary: summary.total=3, summary.succeeded=3, summary.failed=0

✅ test_bulk_update_partial_success [AC2]
   Setup: Create activity-1 (TODO), activity-2 (DONE), and do NOT create activity-99
   Action: PATCH /api/v1/activities/bulk-status with [activity-1, activity-2, activity-99], new_status=BLOCKED
   Verify HTTP: 200 status code
   Verify Response: response.succeeded has 1 item (activity-1), response.failed has 2 items
   Verify Failed: failed[0]={activity_id: "activity-2", error_code: "BUSINESS_RULE_VIOLATION", message: "..."}
   Verify Failed: failed[1]={activity_id: "activity-99", error_code: "NOT_FOUND", message: "..."}
   Verify Repository: activity-1 has status=BLOCKED, activity-2 STILL has status=DONE
   Verify EventBus: exactly 1 TASK_STATUS_CHANGED event (only for activity-1)
   Verify AuditLog: exactly 1 activity log entry (only for activity-1)
   Verify Summary: summary.total=3, summary.succeeded=1, summary.failed=2

✅ test_bulk_update_empty_activity_list [AC3]
   Setup: 1+ activities exist in database
   Action: PATCH /api/v1/activities/bulk-status with activity_ids=[], new_status=DONE
   Verify HTTP: 400 status code (NOT 200)
   Verify Error: error_code="VALIDATION_ERROR", message contains "activity_ids" and "empty"
   Verify Side-Effects: 0 events published, 0 activity logs created, 0 activities modified

✅ test_bulk_update_invalid_status_enum [AC4]
   Setup: 1+ activities exist in database
   Action: PATCH /api/v1/activities/bulk-status with new_status="INVALID_STATUS"
   Verify HTTP: 422 status code (NOT 200)
   Verify Error: error_code="VALIDATION_ERROR", message contains "new_status"
   Verify Side-Effects: 0 events published, 0 activity logs created, 0 activities modified

✅ test_bulk_update_too_many_activities [AC5]
   Setup: Create/mock 101 activity IDs
   Action: PATCH /api/v1/activities/bulk-status with 101 activity_ids, new_status=DONE
   Verify HTTP: 400 status code (NOT 200)
   Verify Error: error_code="VALIDATION_ERROR", message contains "100" or "maximum"
   Verify Side-Effects: 0 activities modified

✅ test_bulk_update_activity_not_found [AC2 edge case]
   Setup: Do NOT create activity-99
   Action: PATCH /api/v1/activities/bulk-status with activity_ids=["activity-99"], new_status=TODO
   Verify HTTP: 200 status code
   Verify Response: response.succeeded is empty, response.failed has 1 item
   Verify Error: failed[0]={activity_id: "activity-99", error_code: "NOT_FOUND"}

✅ test_bulk_update_business_rule_violation [AC2 edge case]
   Setup: Create activity-1 with status=DONE
   Action: PATCH /api/v1/activities/bulk-status with activity_ids=["activity-1"], new_status=BLOCKED
   Verify HTTP: 200 status code
   Verify Response: response.succeeded is empty, response.failed has 1 item
   Verify Error: failed[0]={activity_id: "activity-1", error_code: "BUSINESS_RULE_VIOLATION", message: "Cannot transition..."}

✅ test_bulk_update_single_activity [AC1 edge case]
   Setup: Create 1 activity with status=TODO
   Action: PATCH /api/v1/activities/bulk-status with activity_ids=["activity-1"], new_status=DONE
   Verify HTTP: 200 status code
   Verify Response: response.succeeded has exactly 1 item, response.failed is empty
   Verify Summary: summary.total=1, summary.succeeded=1, summary.failed=0

✅ test_bulk_update_idempotent [Determinism test]
   Setup: Create activity-1, activity-2 with status=TODO
   Action 1: PATCH /api/v1/activities/bulk-status with [activity-1, activity-2], new_status=DONE
   Verify 1: HTTP 200, response.succeeded has 2 items, response.failed is empty, 2 events published
   Action 2: PATCH /api/v1/activities/bulk-status with [activity-1, activity-2], new_status=DONE (same request)
   Verify 2: HTTP 200, response.succeeded is empty, response.failed has 2 items (both BUSINESS_RULE_VIOLATION)
   Verify Consistency: state is deterministic; second call recognizes activities already in target state

✅ test_bulk_update_response_format [Contract compliance]
   Action: PATCH /api/v1/activities/bulk-status with valid request
   Verify: Response has structure { succeeded[], failed[], summary }
   Verify: succeeded[] items are full Activity objects (id, status, updated_at, etc.)
   Verify: failed[] items have {activity_id, error_code, message}
   Verify: summary has {total: int, succeeded: int, failed: int}
   Verify: total == succeeded + failed (deterministic arithmetic)

✅ test_bulk_update_shift_handover_audit_context [Shift-specific]
   Setup: Create 2 activities with status TODO
   Action: PATCH /api/v1/activities/bulk-status with [activity-1, activity-2], new_status=DONE
   Verify: Each activity log entry has details.context = "shift_handover"
   Verify: Audit entries are queryable by activity_id for shift history
```

### Test Coverage Targets

- **Minimum Coverage:** 80% of new code
- **Files Covered:**
  - `src/activities/models.py` - BulkActivityStatusUpdate, BulkActivityStatusUpdateResult, BulkUpdateFailedItem, BulkUpdateSummary models
  - `src/activities/routes.py` - PATCH endpoint
  - `src/activities/service.py` - bulk_update_activities method
  - `src/activities/repository.py` - bulk_update_status method

- **Test Coverage:**
  - ✅ All acceptance criteria verified by tests
  - ✅ All error paths tested (empty list, invalid status, not found, business rule violation)
  - ✅ All events verified (TASK_STATUS_CHANGED published per activity)
  - ✅ All activity logs verified (created per activity)
  - ✅ Partial failure scenario tested
  - ✅ Limits tested (1 activity, 100 activities)
  - ✅ Shift handover audit context verified

---

## Completion Definition

### What Done Looks Like

- [ ] All files modified as specified (routes, service, repository, models)
- [ ] PATCH `/api/v1/activities/bulk-status` endpoint implemented
- [ ] Request model: `BulkActivityStatusUpdate` (activity_ids: list[str], new_status: TaskStatus)
- [ ] Response model: `BulkActivityStatusUpdateResult` (succeeded: list[Task], failed: list[BulkUpdateFailedItem], summary: BulkUpdateSummary)
- [ ] Service method: `bulk_update_activities(activity_ids, new_status)` implemented
- [ ] Repository method: `bulk_update_status(activity_ids, new_status)` implemented
- [ ] All 5 acceptance criteria passed (AC1-AC5)
- [ ] All 11 required tests pass (green)
- [ ] Coverage >= 80% for new code
- [ ] mypy: 0 errors (`mypy src`)
- [ ] ruff: 0 violations (`ruff check src`)
- [ ] All TASK_STATUS_CHANGED events published correctly (per successful update)
- [ ] Activity log entries created per successfully updated activity with shift_handover context
- [ ] No rule violations (all 10 architecture rules compliant)
- [ ] Code review approved
- [ ] Ready for Evaluator assessment

---

## Implementation Notes

### Route → Service → Repository Layering (EXPLICIT ARCHITECTURE)

**Layer 1: Route Handler (routes.py)**
```python
@router.patch("/bulk-status", response_model=BulkActivityStatusUpdateResult, status_code=200)
async def bulk_update_activity_status(
    bulk_update: BulkActivityStatusUpdate,
    service: ActivitiesService = Depends(get_activities_service),
) -> BulkActivityStatusUpdateResult | AppErrorResponse:
    """
    Route responsibilities:
    - Accept HTTP request with BulkActivityStatusUpdate Pydantic model
    - Call service method only (NO repository calls, NO business logic)
    - Catch AppError exceptions and convert to HTTPException
    - Return response model
    """
    try:
        return await service.bulk_update_activities(
            activity_ids=bulk_update.activity_ids,
            new_status=bulk_update.new_status
        )
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
```

**Layer 2: Service (service.py)**
```python
async def bulk_update_activities(
    self,
    activity_ids: list[str],
    new_status: TaskStatus,
) -> BulkActivityStatusUpdateResult:
    """
    Service responsibilities:
    - Validate ALL inputs (empty list, too many activities, invalid status enum)
    - If validation fails: raise AppError (don't process any activities)
    - Process each activity independently via repository
    - Check business rules (allowed transitions per TaskStatus)
    - For each activity: {exists? + transition allowed?} → update or add to failed list
    - Publish TASK_STATUS_CHANGED event per successful update
    - Create activity log entry per successful update (with shift_handover context)
    - Return BulkActivityStatusUpdateResult with succeeded[], failed[], summary
    """
```

**Layer 3: Repository (repository.py)**
```python
async def bulk_update_status(
    self,
    activity_ids: list[str],
    new_status: TaskStatus,
) -> list[Task]:
    """
    Repository responsibilities:
    - Perform atomic update operation for each activity ID
    - Return list of Activity objects with updated status
    - NO validation, NO business logic
    - Raise exceptions only if I/O fails (not for business rules)
    """
```

### Partial Failure Algorithm (DETERMINISTIC FLOW)

**Phase 1 - Request Validation (before any activity processing):**
- Validate activity_ids not empty → if empty, raise ValidationError(400)
- Validate activity_ids length ≤ 100 → if > 100, raise ValidationError(400)
- Validate new_status in TaskStatus enum → if invalid, raise ValidationError(422)
- **STOP if any validation fails; return error immediately; NO activities modified**

**Phase 2 - Per-Activity Processing (if Phase 1 passes):**
- Initialize: succeeded[] = [], failed[] = []
- FOR EACH activity_id in request:
  - Get activity from repository (→ NOT_FOUND? add to failed[])
  - Check if transition allowed (→ BUSINESS_RULE_VIOLATION? add to failed[])
  - If valid: update repository, publish event, log activity, add to succeeded[]
- **NO short-circuit; process ALL activities**

**Phase 3 - Response (always Phase 3 if Phase 1 passed):**
- Return HTTP 200 with { succeeded[], failed[], summary }
- **ALWAYS HTTP 200 for partial/full success**

**Determinism Rules:**
- Request-level validation errors = HTTP 400/422, NO activities updated
- Per-activity errors = HTTP 200 with activity in failed[] list
- Every activity processed exactly once
- No activity update occurs if ANY request-level validation fails
- succeeded[] + failed[] = total activity_ids count (deterministic)

### Audit Trail: Activity Log Entry (ONE per successful update)

**Triggered:** After repository.bulk_update_status() succeeds for each activity

**Record Structure (deterministic):**
```python
activity_log_entry = {
    "activity_id": "activity-1",
    "action": "status_changed",
    "details": {
        "old_status": "TODO",
        "new_status": "DONE",
        "bulk_update": True,
        "context": "shift_handover",  # Shift-specific context
        "timestamp": "2026-08-29T21:55:00Z"
    },
    "created_by": current_user_id,
    "created_at": "2026-08-29T21:55:00Z"
}
```

**Timing:** Activity log entry created AFTER repository update succeeds, BEFORE event published

### Cross-Module Communication: EventBus Only

**Event Type:** `TASK_STATUS_CHANGED` (published to EventBus)

**Triggered:** After repository.bulk_update_status() succeeds AND activity log entry created

**Event Payload Structure (deterministic, per activity):**
```python
event_payload = {
    "activity_id": "activity-1",
    "old_status": "TODO",
    "new_status": "DONE",
    "updated_at": "2026-08-29T21:55:00Z",
    "updated_by": current_user_id,
    "bulk_update": True,
    "context": "shift_handover"
}
```

**Publishing Timing:** One event published PER successfully updated activity, in order

**EventBus Rule:** No other modules call ActivitiesService directly; all communication flows through EventBus

---

**Status:** `AWAITING_APPROVAL`  
**Approval Needed:** Product Owner (business logic) + Architecture Lead (compliance)  
**Next Phase:** Code generation by Generator agent  
**Estimated Duration:** 30-45 minutes model time

**Determinism Guarantee:** This contract defines behavior exhaustively. Generator implementation must match every specification. Evaluator will verify deterministic compliance.

## Verification Checklist (10-Point Review)

This sprint contract has been reviewed against 10 explicit criteria:

| # | Criterion | Section | Verification |
|---|-----------|---------|--------------|
| 1 | PATCH request/response behavior explicit | Architecture Contract + Implementation Notes | ✅ Full HTTP semantics, data flow, method signatures defined |
| 2 | Partial success/failure behavior deterministic | AC2, Implementation Notes | ✅ Algorithm documented; every activity outcome specified |
| 3 | Every successful update produces audit entry | Implementation Notes (Audit Trail section) | ✅ One log entry guaranteed per successful update |
| 4 | Invalid, missing, non-updatable IDs have outcomes | AC3-AC5 + Implementation Notes | ✅ All error scenarios have explicit HTTP status + error_code |
| 5 | Route→Service→Repository layering preserved | Implementation Notes (Layer Responsibilities) | ✅ Method signatures per layer; data flow explicit |
| 6 | Cross-module side effects use EventBus only | Implementation Notes (EventBus section) | ✅ EventBus-only communication; timing explicit |
| 7 | Every AC in GIVEN/WHEN/THEN format | AC1-AC5 sections | ✅ All 5 ACs fully formatted as GIVEN/WHEN/THEN |
| 8 | Every AC mapped to ≥1 test | Test Contract (AC→Test Mapping table) | ✅ Explicit 1-to-many mapping: every AC has primary + secondary tests |
| 9 | Scope/out-of-scope explicit | Dependencies section + spec.md | ✅ Scope: independent; no blocking dependencies |
| 10 | Status: AWAITING_APPROVAL | Below | ✅ Status retained |

---

*This contract defines the concrete, testable, deterministic implementation requirements for ACTIVITIES-003 (Shift Handover Bulk Update). Generator uses this as source of truth. Evaluator uses this to verify completion with zero ambiguity.*
