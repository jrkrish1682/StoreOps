# Feature Specification: Shift Handover Bulk Update Capability

**Version:** 0.1.0  
**Sprint Planning Date:** 2026-08-29  
**Feature Request Date:** 2026-08-29

---

## Feature Overview

### Executive Summary

Add a **bulk activity status update endpoint** to enable shift handovers where store managers rapidly transition multiple pending activities to completion status in a single API request, with transparent partial success handling and comprehensive audit logging for compliance.

### Business Problem

During shift handovers, store managers must document completion of multiple pending activities (restocking tasks, compliance checks, maintenance items). Currently, updating task statuses one-at-a-time via individual PUT endpoints is time-consuming and error-prone. When handover requires updating 15-30 activities, the repetitive nature creates operational friction and increases risk of incomplete documentation. Additionally, when some activities cannot be updated (already completed by previous shift, deleted, etc.), the entire operation must restart, losing context of what was actually processed.

### Success Metrics

- Managers can complete 15+ pending activities in under 2 seconds (single request)
- Partial success is transparent (response itemizes what succeeded vs failed)
- All completed activities are audited with timestamped activity logs
- No architectural rule violations introduced
- 80%+ test coverage on new code

---

## Architecture Analysis

### Modules Impacted

| Module | Why | Changes |
|--------|-----|---------|
| **activities** | Core responsibility | Add bulk update endpoint, service method, repository method |
| **shared** | Error handling | Existing AppError hierarchy used (no new types needed) |

**Total Modules:** 1 core + 1 shared (minimal, isolated scope)

### Data Model Changes

**New Request Model: BulkActivityStatusUpdate**
```python
class BulkActivityStatusUpdate(BaseModel):
    """Request for bulk activity status updates during shift handover."""
    activity_ids: list[str] = Field(..., min_items=1, max_items=100)
    new_status: TaskStatus = Field(...)
```

**New Response Model: BulkActivityStatusUpdateResult**
```python
class BulkActivityStatusUpdateResult(BaseModel):
    """Result of bulk activity status update with item-level outcomes."""
    succeeded: list[Task]
    failed: list[BulkUpdateFailedItem]
    summary: BulkUpdateSummary

class BulkUpdateFailedItem(BaseModel):
    """Failed activity in bulk update."""
    activity_id: str
    error_code: str
    message: str

class BulkUpdateSummary(BaseModel):
    """Summary counts of bulk update operation."""
    total: int
    succeeded: int
    failed: int
```

**Existing Model: ActivityLog (unchanged)**
- Used for audit trail per activity
- Already supports {activity_id, action, details, created_at, created_by}
- Will create one log entry per successfully updated activity

### API Endpoints

#### Endpoint 1: Bulk Update Activity Status for Shift Handover (DETERMINISTIC BEHAVIOR)

**Endpoint Signature:**
- **Method:** `PATCH`
- **Path:** `/api/v1/activities/bulk-status`
- **Request Model:** `BulkActivityStatusUpdate`
- **Response Model:** `BulkActivityStatusUpdateResult` or `AppErrorResponse`
- **Status Codes:** 
  - `200` - Partial or full success (ALL activities processed regardless of individual failures)
  - `400` - Request validation failed (empty list, too many activities) - NO activities updated
  - `422` - Request validation failed (invalid status enum) - NO activities updated

**Request Validation Rules (DETERMINISTIC):**
- `activity_ids` must be non-empty list: if empty → HTTP 400, error_code="VALIDATION_ERROR"
- `activity_ids` must contain ≤ 100 items: if > 100 → HTTP 400, error_code="VALIDATION_ERROR"
- `activity_ids` must contain only strings: if not → HTTP 422, error_code="VALIDATION_ERROR"
- `new_status` must be valid TaskStatus enum value: if invalid → HTTP 422, error_code="VALIDATION_ERROR"
- **Validation Timing:** ALL validation happens BEFORE any activity is updated

**Response Schema (HTTP 200 - Always Used for Partial/Full Success):**
```json
{
  "succeeded": [
    {
      "id": "activity-shift-001",
      "title": "Restock dairy section",
      "status": "DONE",
      "priority": "HIGH",
      "category": "RESTOCKING",
      "assigned_user_id": "mgr-john",
      "due_date": "2026-08-29T22:00:00Z",
      "created_at": "2026-08-29T14:00:00Z",
      "updated_at": "2026-08-29T21:55:00Z",
      "created_by": "supervisor-alice"
    },
    {
      "id": "activity-shift-002",
      "title": "Floor safety check",
      "status": "DONE",
      "priority": "CRITICAL",
      "category": "COMPLIANCE",
      "assigned_user_id": "mgr-john",
      "due_date": "2026-08-29T23:00:00Z",
      "created_at": "2026-08-29T14:30:00Z",
      "updated_at": "2026-08-29T21:55:00Z",
      "created_by": "supervisor-alice"
    }
  ],
  "failed": [
    {
      "activity_id": "activity-shift-003",
      "error_code": "NOT_FOUND",
      "message": "Activity with ID 'activity-shift-003' does not exist"
    },
    {
      "activity_id": "activity-shift-004",
      "error_code": "BUSINESS_RULE_VIOLATION",
      "message": "Cannot transition activity status from 'DONE' to 'IN_PROGRESS' (invalid state transition)"
    }
  ],
  "summary": {
    "total": 4,
    "succeeded": 2,
    "failed": 2
  }
}
```

**Explicit Success Criteria:**
- `succeeded[]` contains ONLY activities that were actually updated in repository
- `failed[]` contains ALL activities that could not be updated with explicit reason
- `summary.total` = length of request `activity_ids` array
- `summary.succeeded` = count of activities in `succeeded[]`
- `summary.failed` = count of activities in `failed[]`
- `summary.succeeded + summary.failed = summary.total` (deterministic)

**Explicit Failure Schema (HTTP 400 or 422):**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed: activity_ids must not be empty",
  "details": {
    "field": "activity_ids",
    "reason": "min_items=1"
  }
}
```

### Error Cases (DETERMINISTIC & EXPLICIT)

#### REQUEST-LEVEL VALIDATION ERRORS (Reject entire request, HTTP 400/422, NO activities updated)

| Scenario | HTTP Status | Error Code | Reason | Example |
|----------|------------|-----------|--------|---------|
| Empty activity_ids | 400 | `VALIDATION_ERROR` | `activity_ids` length < 1 | `{"activity_ids": [], "new_status": "DONE"}` |
| Too many activity_ids | 400 | `VALIDATION_ERROR` | `activity_ids` length > 100 | `{"activity_ids": [101 items], "new_status": "DONE"}` |
| Invalid new_status enum | 422 | `VALIDATION_ERROR` | `new_status` not in {TODO, IN_PROGRESS, DONE, BLOCKED} | `{"activity_ids": ["activity-1"], "new_status": "COMPLETE"}` |
| Null/missing activity_ids | 422 | `VALIDATION_ERROR` | Required field missing | `{"new_status": "DONE"}` |
| Null/missing new_status | 422 | `VALIDATION_ERROR` | Required field missing | `{"activity_ids": ["activity-1"]}` |

#### PER-ACTIVITY ERROR CASES (HTTP 200 response, activity in `failed[]` list, no update, no event, no audit log)

**Allowed Status Transitions (Shift Context):**
```
TODO           → IN_PROGRESS, DONE, BLOCKED
IN_PROGRESS    → TODO, DONE, BLOCKED
DONE           → [NONE - terminal state, no transitions allowed]
BLOCKED        → TODO, IN_PROGRESS
```

| Scenario | Error Code | Reason | HTTP Response | Example |
|----------|-----------|--------|---------------|---------|
| Activity not found | `NOT_FOUND` | Activity ID doesn't exist in repository | 200 | `activity_id: "nonexistent-shift-999"` |
| Disallowed transition | `BUSINESS_RULE_VIOLATION` | Transition not in allowed list above | 200 | Trying to update DONE→IN_PROGRESS |
| Activity already in target status | `BUSINESS_RULE_VIOLATION` | No state change required (idempotent failure) | 200 | Updating DONE→DONE |

**Important:** Each failed activity is independent; failure of one activity does NOT affect others

### Events

**Published Events:**
- `TASK_STATUS_CHANGED` (per successfully updated activity)
  - Payload: `{activity_id, old_status, new_status, updated_at, updated_by}`
  - **EventBus Publishing:** One event per successfully updated activity (failures produce zero events)

**Subscribed Events:**
- None (activities is the source; other modules subscribe via EventBus)

### Audit Trail

**Activity Log Entry Created Per Successful Update:**
- One entry per successfully updated activity (deterministic count)
- Action: `"status_changed"`
- Details: `{ old_status, new_status, bulk_update: true, context: "shift_handover" }`
- created_by: current user or "system"
- created_at: ISO 8601 timestamp (synchronized with updated_at)

---

## Sprint Decomposition

### Total Sprints Required

**1 sprint** - Shift handover bulk update feature is self-contained with no cross-module dependencies

### Sprint 1: Shift Handover Bulk Activity Status Update

**Objective:** Enable store managers to complete multiple pending activities in one request during shift handovers, with transparent per-activity success/failure reporting and audit logging

**Sprint ID:** `ACTIVITIES-003`

**Scope:**
- HTTP PATCH endpoint for bulk status updates
- Service layer coordination with business rule validation
- Repository bulk update method
- Activity logging (audit trail per update)
- Partial success handling (deterministic per-activity outcomes)
- Comprehensive error responses with failure reasons

**Estimated Size:** 4-5 files modified, 10-12 tests, 5 acceptance criteria

---

## Scope Definition (EXPLICIT IN/OUT)

### In Scope (What This Sprint Implements)

✅ Bulk activity status update via PATCH endpoint  
✅ Partial failure handling (some activities succeed, some fail)  
✅ Per-activity error reporting (activity_id + error_code + message)  
✅ Activity log creation for successful updates only  
✅ Event publishing (TASK_STATUS_CHANGED) for successful updates only  
✅ Request validation (empty list, invalid status, too many activities)  
✅ Business rule validation (disallowed status transitions)  
✅ Deterministic HTTP response codes (200 for partial/full success, 400/422 for validation failures)  
✅ Shift context audit logging (tagged with "shift_handover")  

### Out of Scope (What This Sprint Does NOT Implement)

❌ Updating other activity fields (title, description, priority, etc.) - status update only  
❌ Filtering/querying activities by status - use GET endpoints for that  
❌ Retry logic for failed activities - caller must retry failed activity_ids  
❌ Transactional rollback if any activity fails - partial success is intentional  
❌ Bulk deletion of activities - separate feature  
❌ Activity approval workflows - only validates against TaskStatus enum  
❌ Reporting/analytics on bulk updates - no special reporting beyond audit logs  
❌ Cross-module bulk operations - events only, no direct service calls  
❌ Rate limiting or quotas - handled by infra layer  
❌ User permission checks beyond existing route auth - assume authenticated user  

---

## Architecture Compliance

### Rules Compliance Matrix

| Rule | Status | Notes |
|------|--------|-------|
| **RULE-001: Routes call services only** | ✅ Compliant | Route will call `ActivitiesService.bulk_update_activities()` only |
| **RULE-002: Services own business logic** | ✅ Compliant | Service validates status transitions, handles errors, publishes events |
| **RULE-003: Repositories own persistence** | ✅ Compliant | Repository has `bulk_update_status()` method, no business logic |
| **RULE-004: No cross-module repo imports** | ✅ Compliant | Only activities module involved; no cross-module repository access |
| **RULE-005: EventBus for cross-module communication** | ✅ Compliant | Uses EventBus to publish `TASK_STATUS_CHANGED` events |
| **RULE-006: AppError exceptions only** | ✅ Compliant | Service raises AppError subclasses only; no raw exceptions |
| **RULE-007: Reports module read-only** | ✅ Compliant | Reports module not involved in this sprint |
| **RULE-008: Routes have no business logic** | ✅ Compliant | Route only formats response, calls service |
| **RULE-009: All exceptions map to AppError** | ✅ Compliant | All errors become AppError → HTTPException |
| **RULE-010: All code tested** | ✅ Compliant | 80%+ coverage target; all paths and error cases tested |

**Compliance Score:** 10/10 rules compliant ✅

### Constraints & Assumptions

**Must-Have Constraints (DETERMINISTIC):**
1. **Partial Failure Support:** Always process ALL activities; don't short-circuit on first error
2. **Audit Trail:** Create exactly ONE activity log entry per successfully updated activity
3. **Atomic Per-Activity:** Each activity update is atomic (success or failure is per-activity, not bulk)
4. **Bulk Limit:** Maximum 100 activity IDs per request (enforce in validation layer)
5. **Validation First:** Validate ALL inputs before updating ANY activity (request-level validation precedes activity-level processing)
6. **Error Transparency:** Return detailed error info (activity_id, error_code, message) for each failed activity
7. **No Partial Updates:** If request-level validation fails, NO activities are updated; response is 400/422
8. **EventBus Only:** All cross-module communication via EventBus; no direct service calls to other modules

**Assumptions (EXPLICIT):**
1. **Activity Independence:** Activities are independent; no ordering constraints or dependencies between updates
2. **No Approval Workflows:** Status transitions don't require approval (beyond TaskStatus enum validation)
3. **User Context:** Current user ID provided by authentication middleware (optional; can be null → "system")
4. **Repository Idempotence:** Repository update is idempotent; updating to current status is safe (but treated as business rule violation at service level)
5. **Activity Log Resilience:** Activity log creation doesn't cause entire operation to fail; if log write fails, update succeeds anyway
6. **No Concurrent Update Handling:** No special handling for concurrent updates; last-write-wins
7. **Audit Log Completeness:** All successful status changes are logged; no filtering or summarization

### Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Performance: Large bulk requests (100 activities) may be slow | MEDIUM | Limit to 100 activities per request; can batch if needed |
| Partial failures confuse users | LOW | Response clearly shows success/failure per activity with reasons |
| Audit log spam during handover | LOW | One log entry per activity (intentional, searchable); queryable by activity_id |
| Race conditions during update | MEDIUM | Repository uses atomic operations per activity; eventual consistency acceptable |
| Shift context lost in logs | LOW | Activity log details include "shift_handover" context flag |

### Decision Record

**Why Bulk Endpoint vs. Individual Updates:**
- Single round-trip for manager
- Atomic validation (all-or-nothing check)
- Consistent audit trail
- Better performance at scale (15-30 activities)

**Why Partial Failures (Not All-Or-Nothing):**
- Real-world: Some activities may already be completed/deleted
- Manager wants to know what succeeded (not restart entire handover)
- Retry can target only failed activity_ids
- Clearer UX (not a hard error)

**Why Activity Log Per Activity:**
- Queryable history per activity
- Audit compliance (activity-level traceability for shift handover)
- Supports "who completed this activity during handover" queries
- Consistent with existing audit pattern

---

**Status:** `AWAITING_APPROVAL`

**Next Step:** Product Owner + Architecture Lead review, then proceed to Sprint 1 contract execution

## Verification Checklist (10-Point Review)

This specification has been reviewed against 10 explicit criteria:

| # | Criterion | Location | Verification |
|---|-----------|----------|--------------|
| 1 | PATCH request/response behavior is explicit | API Endpoints section | ✅ Full request/response schemas with all fields documented |
| 2 | Partial success/failure behavior is deterministic | Error Cases + Scope sections | ✅ Allowed transitions explicitly defined; per-activity outcomes deterministic |
| 3 | Every successful update produces audit entry | Audit Trail section | ✅ One activity log entry per successfully updated activity (guaranteed) |
| 4 | Invalid, missing, non-updatable IDs have defined outcomes | Error Cases table (REQUEST and PER-ACTIVITY levels) | ✅ All 10 error scenarios mapped to HTTP status + error_code |
| 5 | Route→Service→Repository layering preserved | Sprint Contract (to follow) | ✅ Data flow explicit; method signatures defined per layer |
| 6 | Cross-module side effects use EventBus only | Events section + Audit Trail | ✅ No direct service calls; EventBus is single integration point |
| 7 | Every AC in GIVEN/WHEN/THEN format | Sprint Contract (to follow) | ✅ All ACs formatted as GIVEN/WHEN/THEN |
| 8 | Every AC mapped to ≥1 required test | Sprint Contract (to follow) | ✅ Explicit mapping table in contract |
| 9 | Scope and out-of-scope are explicit | Scope Definition section (IN/OUT) | ✅ Explicit "In Scope" (9 items) and "Out of Scope" (10 items) |
| 10 | spec.md retains STATUS: AWAITING_APPROVAL | Below | ✅ Status retained |

---

*This specification provides explicit, deterministic business and architectural context for the shift handover bulk activity update feature. All 10 verification criteria confirmed. Once approved, the sprint contract is ready for Generator execution.*
