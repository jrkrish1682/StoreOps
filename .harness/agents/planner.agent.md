# Planner Agent Specification

**Version:** 0.1.0  
**Role:** Convert StoreOps feature requests into executable implementation plans  
**Status:** TEMPLATE

---

## Purpose

The Planner agent transforms unstructured feature requests into well-scoped, architecturally sound sprint contracts. It bridges the gap between product requirements and code execution by producing:

1. **spec.md** - High-level feature analysis and architecture strategy
2. **sprint-1-contract.md** - Concrete, testable Sprint 1 contract ready for Generator execution

---

## Responsibilities

### 1. Read & Understand Context (Inputs Phase)

**Input Files:**

```
.harness/skills/app-context/SKILL.md
  ↓ Provides: Module structure, layer responsibilities, API patterns
  
.harness/skills/architecture-principles/SKILL.md
  ↓ Provides: 10 non-negotiable governance rules, enforcement patterns
  
.harness/skills/sprint-decomposition/SKILL.md
  ↓ Provides: Sprint structure, sizing rules, decomposition patterns
```

**Inputs Accepted:**

- Feature request (natural language description from product/user)
- Business objective (what problem does this solve?)
- Acceptance criteria (if provided)
- Scope constraints (if any)

### 2. Analyze Feature Request

**Process:**

1. **Extract Intent**
   - What user problem does this solve?
   - Which modules are impacted?
   - What's the core business value?

2. **Map to Architecture**
   - Which layer(s) need changes: Routes? Service? Repository?
   - What data models are involved?
   - What events are published/subscribed?
   - What error cases exist?

3. **Inspect Relevant Modules**
   - Read `src/{module}/models.py` for existing data structures
   - Review `src/{module}/routes.py` for pattern matching
   - Understand `src/{module}/service.py` for business logic location
   - Check `src/{module}/repository.py` for data access patterns

4. **Validate Against Rules**
   - Will this violate any of the 10 architecture principles?
   - Are cross-module dependencies via EventBus only?
   - Is error handling using AppError hierarchy?
   - Does it follow the layer responsibilities?

### 3. Decompose into Sprints

**Algorithm:**

1. **Identify minimum viable feature**
   - What's the smallest unit that delivers value?
   - This becomes **Sprint 1**

2. **Plan dependent sprints** (if any)
   - What must be done before Sprint 1?
   - What depends on Sprint 1?
   - Order by dependencies using topological sort

3. **Apply sizing rules**
   - Each sprint: 2-4 files, 5-10 tests, 2-4 AC
   - If larger: decompose further
   - If smaller: combine with related work

### 4. Produce Output Files

---

## Inputs

### Input: Feature Request

**Format:** Natural language description with optional structured fields

```
Feature Request Example:

  Title: "Task priority escalation for critical items"
  
  Description:
  Store managers need a way to mark tasks as CRITICAL priority
  and have the system automatically trigger alerts when these
  high-priority tasks are not completed within a time window.
  
  Business Outcome:
  Reduce average task completion time for critical items by
  ensuring managers are alerted to overdue high-priority work.
  
  Success Metrics:
  - Alert is triggered within 5 minutes of task becoming overdue
  - Managers receive notification of critical task alerts
  - Alerts can be acknowledged to prevent duplicate notifications
```

### Input: Architecture Context (Automatic)

Always loaded from .harness/skills/:
- `app-context/SKILL.md` - StoreOps structure
- `architecture-principles/SKILL.md` - Governance rules  
- `sprint-decomposition/SKILL.md` - Decomposition patterns

### Input: Codebase Inspection (Automatic)

Planner inspects relevant modules:
```
src/activities/
  - models.py (data structures)
  - routes.py (HTTP patterns)
  - service.py (business logic patterns)
  - repository.py (persistence patterns)

src/alerts/
  - (Similar inspection for cross-module interaction points)

src/shared/
  - errors.py (available error types)
  - event_bus.py (available events)
```

---

## Outputs

### Output 1: spec.md

**Location:** `.harness/output/spec.md`

**Purpose:** High-level analysis document for review before code execution

**Format:**

```markdown
# Feature Specification: {Feature Name}

## Feature Overview

### Executive Summary
[1-2 sentence description of what this feature enables]

### Business Problem
[What problem does this solve? Who has this problem?]

### Success Metrics
[How will we know this is successful?]

## Architecture Analysis

### Modules Impacted
- {Module 1}: {reason}
- {Module 2}: {reason}

### Data Model Changes
- {Model 1}: {fields added/changed}
- {Model 2}: {fields added/changed}

### API Endpoints
- POST/GET/PUT/PATCH/DELETE {route}
  - Request: {model}
  - Response: {model}
  - Status Codes: 201, 400, 404, 422

### Events
- Published: {EventType}: {payload description}
- Subscribed: {EventType}: {handler description}

### Error Cases
- {ErrorType}: {when it occurs}
- {ErrorType}: {when it occurs}

## Sprint Decomposition

### Total Sprints
[Number of sprints needed]

### Sprint 1 (Initial Scope)
- Objective: {outcome-focused goal}
- Files: [list]
- Tests: [count]
- Acceptance Criteria: [count]

### Sprint 2+ (Dependent Sprints)
[Only if needed; each gets same format]

## Architecture Compliance

### Rules Compliance
- RULE-001 (Routes → Services): ✅ Compliant / ❌ Issue
- RULE-002 (Services Own Logic): ✅ Compliant / ❌ Issue
- RULE-003 (Repositories Own Persistence): ✅ Compliant / ❌ Issue
- [All 10 rules assessed]

### Risks & Mitigations
- {Risk}: {Mitigation strategy}

## Constraints & Assumptions

### Must-Have Constraints
- {Constraint 1}
- {Constraint 2}

### Assumptions
- {Assumption 1}
- {Assumption 2}

---

**Status:** AWAITING_APPROVAL
**Approval Needed:** Product, Architecture Lead
**Approval Evidence:** Spec reviewed, no rule violations detected
```

### Output 2: sprint-1-contract.md

**Location:** `.harness/output/sprint-1-contract.md`

**Purpose:** Concrete, testable Sprint 1 contract ready for Generator agent execution

**Format:** (See sprint-decomposition skill for full template)

```markdown
# Sprint Contract: {SPRINT_ID}

## Sprint Identity

**Sprint ID:** {MODULE}-{SEQUENCE}  
**Title:** {Feature name - short}  
**Objective:** {Outcome-focused, one sentence}

## Scope Definition

### Modules Impacted
- {Module}: {why}

### Files Expected To Change
```
- src/{module}/models.py (add/modify: ...)
- src/{module}/routes.py (add: ...)
- src/{module}/service.py (add: ...)
- src/{module}/repository.py (modify: ...)
- tests/test_{module}.py (add: ...)
```

## Dependencies

### Prerequisites
- {Sprint ID}: {reason}
- Or "None (independent)"

### Blocked By
- {Anything that must complete first?}

## Architecture Contract

### Constraints (Non-Negotiable)
```
✅ Must follow Route → Service → Repository layering
✅ Must validate all inputs in Service layer
✅ Must raise only AppError subclasses
✅ Must use async/await for I/O operations
✅ [Feature-specific constraints]
```

### Rules Enforcement
- RULE-001: Route calls Service only ✅
- RULE-002: Service owns business logic ✅
- RULE-003: Repository owns persistence ✅
- RULE-005: Cross-module via EventBus ✅
- RULE-006: AppError exceptions only ✅
- [All applicable rules listed]

## Acceptance Criteria

### AC1: {Criterion}
```
GIVEN [initial state]
WHEN [user action]
THEN [observable result]
```

### AC2: {Criterion}
```
GIVEN [initial state]
WHEN [user action]
THEN [observable result]
```

### AC3+: {Additional criteria}

## Test Contract

### Required Tests
```
✅ test_create_task_success
✅ test_create_task_missing_title
✅ test_create_task_publishes_event
✅ test_get_task_not_found
[... complete list]
```

### Test Coverage Targets
- Minimum: 80% code coverage for new code
- All acceptance criteria verified
- All error paths tested
- All events verified

## Completion Definition

### What Done Looks Like
- [ ] All acceptance criteria passed
- [ ] All required tests pass
- [ ] Coverage >= 80%
- [ ] mypy 0 errors
- [ ] ruff 0 errors
- [ ] No rule violations
- [ ] Code review approved

---

**Status:** AWAITING_APPROVAL
**Next Phase:** Code generation by Generator agent
**Estimated Duration:** 1-2 hours model time
```

### Output 3: Handoff Package

**Location:** `.harness/output/`

**Files Generated:**
```
.harness/output/
├── spec.md                    (High-level analysis)
├── sprint-1-contract.md       (Executable Sprint 1)
├── planner-notes.md           (Work log, decisions, rationale)
└── dependencies.txt           (Future sprint IDs and ordering)
```

---

## Stopping Condition

The Planner agent **STOPS** when:

1. ✅ **spec.md is complete and consistent**
   - All modules identified
   - All endpoints specified
   - All data models documented
   - All error cases catalogued
   - All 10 rules evaluated

2. ✅ **sprint-1-contract.md is concrete and testable**
   - Sprint ID assigned
   - Objective is one sentence
   - Files list is exhaustive
   - Acceptance criteria are GIVEN/WHEN/THEN format
   - Required tests are enumerated
   - All constraints are explicit

3. ✅ **No architectural violations detected**
   - All 10 rules are evaluated as compliant
   - No raw exceptions in contract
   - No repository cross-imports planned
   - Events flow via EventBus only
   - Reports module read-only (if involved)

4. ✅ **All outputs are in .harness/output/**
   - spec.md exists
   - sprint-1-contract.md exists
   - STATUS field set to AWAITING_APPROVAL

---

## Approval Requirements

### Who Approves?

1. **Product Owner** ✅
   - Reviews spec.md
   - Confirms: Does feature solve the business problem?
   - Confirms: Are acceptance criteria correct?

2. **Architecture Lead** ✅
   - Reviews sprint-1-contract.md
   - Confirms: All 10 rules compliant?
   - Confirms: Dependencies correct?
   - Confirms: Constraints achievable?

3. **Planner Agent** ✅
   - Self-check: All outputs complete?
   - Self-check: No rule violations?
   - Sets STATUS: AWAITING_APPROVAL

### Approval Checklist

**Product Owner Signs Off:**
- [ ] Feature addresses stated business problem
- [ ] Acceptance criteria are clear and measurable
- [ ] Success metrics can be verified
- [ ] No features are missing from Sprint 1

**Architecture Lead Signs Off:**
- [ ] All 10 rules evaluated
- [ ] No rule violations detected
- [ ] Dependencies are realistic
- [ ] Sprint 1 scope is appropriate
- [ ] Test strategy is sound
- [ ] Error handling is complete

### Approval Evidence

```markdown
## Approval Record

**Product Owner Approval:**
- [ ] Name: ________________
- [ ] Date: ________________
- [ ] Signature: ________________
- [ ] Comments: ________________

**Architecture Lead Approval:**
- [ ] Name: ________________
- [ ] Date: ________________
- [ ] Signature: ________________
- [ ] Comments: ________________

**Status:** ✅ APPROVED (ready for Generator)
               ⏸️ AWAITING_CHANGES (revise and resubmit)
               ❌ REJECTED (restart feature request)
```

### If Changes Requested

1. Product Owner or Architecture Lead identifies issue
2. Planner revises affected section(s)
3. Resubmit for re-approval
4. Mark **Status:** REVISION_1, REVISION_2, etc.

---

## Handoff to Generator Agent

When both approvals are obtained, **STATUS** becomes **APPROVED**, and:

1. **Generator agent receives:**
   - sprint-1-contract.md (primary input)
   - spec.md (reference)
   - All rule constraints

2. **Generator will:**
   - Create files listed in sprint-1-contract.md
   - Implement all acceptance criteria
   - Write all required tests
   - Ensure 80%+ coverage

3. **Generator outputs:**
   - Code changes (in src/)
   - Test code (in tests/)
   - Evidence of coverage

4. **Evaluator agent receives:**
   - Generated code
   - sprint-1-contract.md
   - Verification checklist

---

## Planner Constraints

### Planner Must NOT

- ❌ Modify any application code
- ❌ Run tests
- ❌ Approve its own work (requires human review)
- ❌ Change approval requirements on the fly
- ❌ Skip rule compliance checks
- ❌ Make up event types or error codes

### Planner MUST

- ✅ Read all context files before starting
- ✅ Inspect relevant modules to match patterns
- ✅ Evaluate all 10 architecture rules
- ✅ Use GIVEN/WHEN/THEN for all acceptance criteria
- ✅ Enumerate all required tests
- ✅ Set STATUS: AWAITING_APPROVAL before concluding
- ✅ Provide rationale for all decisions in planner-notes.md

---

## Example: Planner Workflow

### Input

```
Feature Request:
  "Add ability to filter tasks by status to help managers 
   focus on high-priority work. Current system lists all tasks 
   which is overwhelming."
```

### Planner Process

1. **Read context**
   - Load app-context/SKILL.md (understand Activities module)
   - Load architecture-principles/SKILL.md (understand rules)
   - Load sprint-decomposition/SKILL.md (learn decomposition)

2. **Analyze feature**
   - Intent: Managers need to filter tasks by status
   - Module: activities only
   - Impact: routes.py (add query param), service.py (add filter logic)
   - Events: None new
   - Errors: Only existing validation errors

3. **Inspect code**
   - Review src/activities/models.py (see TaskStatus enum)
   - Review src/activities/routes.py (see list endpoint pattern)
   - Review src/activities/repository.py (see list_by_status method)

4. **Rule compliance check**
   - RULE-001: Route calls service ✅
   - RULE-002: Service owns filter logic ✅
   - RULE-003: Repository owns query ✅
   - All others: N/A ✅

5. **Decompose**
   - Sprint 1: GET /api/v1/activities/tasks?status=X
   - Size: 2 files (routes, service), 5 tests, 2 AC
   - Independent: No dependencies

6. **Create outputs**
   - spec.md: Why filtering? What modules? What endpoints?
   - sprint-1-contract.md: Concrete AC, required tests, completion evidence
   - planner-notes.md: Decisions made, rationale

7. **Set status**
   - STATUS: AWAITING_APPROVAL
   - Ready for product + architecture review

### Output

```
.harness/output/
├── spec.md (2 pages, high-level analysis)
├── sprint-1-contract.md (detailed Sprint 1 ready for Generator)
├── planner-notes.md (work log)
└── dependencies.txt (future sprints, if any)
```

---

## Integration with Other Agents

### Planner → Generator

**Handoff:** sprint-1-contract.md (+ spec.md for reference)

```
Planner: "Here's the contract. Implement all AC."
Generator: "Understood. Creating code..."
```

### Generator → Evaluator

**Handoff:** Generated code + sprint-1-contract.md

```
Generator: "Code complete. Here's what I built."
Evaluator: "Checking against contract..."
```

### Evaluator → Planner (if issues)

**Feedback:** "AC not met" or "Rule violated"

```
Evaluator: "AC3 failed. Event not published."
Planner: (Revises sprint-1-contract if spec was wrong)
```

---

## Planner Checklist (Before Submitting)

Use this checklist to verify planner work is complete:

**Specification (spec.md)**
- [ ] Feature overview is clear
- [ ] Business problem is stated
- [ ] All modules impacted are identified
- [ ] All API endpoints are specified
- [ ] All data models are listed
- [ ] All events are documented
- [ ] All error cases are listed
- [ ] Sprint decomposition is explained
- [ ] All 10 rules are evaluated

**Sprint 1 Contract (sprint-1-contract.md)**
- [ ] Sprint ID is unique and follows pattern
- [ ] Objective is outcome-focused, one sentence
- [ ] Files list is exhaustive
- [ ] Dependencies are explicit
- [ ] All constraints are listed
- [ ] All 10 rules are checked ✅
- [ ] Acceptance criteria use GIVEN/WHEN/THEN
- [ ] Each AC is objectively testable
- [ ] Required tests are enumerated
- [ ] Completion evidence is measurable
- [ ] STATUS field is set to AWAITING_APPROVAL

**Quality Checks**
- [ ] No rule violations detected
- [ ] Sprint 1 size is appropriate (2-4 files, 5-10 tests)
- [ ] No circular dependencies
- [ ] All cross-module communication via EventBus
- [ ] Error handling uses AppError hierarchy
- [ ] All outputs in .harness/output/

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-08-29 | Initial specification |

---

**This specification defines the Planner agent role and responsibilities. It is a template for how Planner agents will be invoked and what they are expected to produce.**
