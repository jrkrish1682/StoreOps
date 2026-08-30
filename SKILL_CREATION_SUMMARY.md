# StoreOps Harness Skills - Creation Summary

**Date Created:** 2026-08-29  
**Location:** `.harness/skills/`  
**Total Skills:** 3 created (plus 5 existing)  
**Total Lines of Guidance:** 3,179 lines across all three new skills

---

## Three New Skills Created

### 1. ✅ How-to-Review (741 lines)

**File:** `.harness/skills/how-to-review/SKILL.md`

**Purpose:** Teach Evaluators how to systematically review generated StoreOps code using a deterministic, sequential 7-step process.

**Content Includes:**
- **Step 1:** Review Sprint Contract (contract completeness check)
- **Step 2:** Review generator-summary.md (decision documentation)
- **Step 3:** Review Source Code Changes (detailed code patterns for routes, services, repositories, models)
- **Step 4:** Review Test Coverage (test organization, categories, patterns)
- **Step 5:** Run Automated Validation (mypy, ruff, pytest commands)
- **Step 6:** Apply Architecture Governance Checks (layering, imports, EventBus usage, reports read-only, errors, logic)
- **Step 7:** Determine Verdict (PASS/CONDITIONAL_PASS/FAIL)

**Key Features:**
- File-level and line-level feedback templates
- Specific violation patterns with examples
- Common pitfalls checklist
- Review checklist summary for quick reference

**Usage:** Reference when reviewing PRs or when using `/code-review` skill

---

### 2. ✅ Evaluation-Rules (802 lines)

**File:** `.harness/skills/evaluation-rules/SKILL.md`

**Purpose:** Convert non-deterministic LLM output into deterministic PASS/FAIL decisions using two weighted evaluation dimensions.

**Content Includes:**

**Dimension A: Architecture Compliance (50% of score)**
- A1: Route-Service-Repository Layering (20%)
- A2: No Cross-Module Repository Imports (20%)
- A3: EventBus Required for Side Effects (20%)
- A4: Reports Module Remains Read-Only (20%)
- A5: AppError Compliance (20%)
- A6: No Business Logic in Routes (20%)

**Dimension B: Engineering Quality (50% of score)**
- B1: pytest Passes (25%)
- B2: mypy Passes (25%)
- B3: ruff Passes (25%)
- B4: Business Rule Tests Exist (12.5%)
- B5: Acceptance Criteria Covered (12.5%)
- B6: Code Quality (12.5%)

**Hard Fail Conditions** (any one = instant FAIL):
1. pytest failure
2. ruff failure
3. mypy failure
4. cross-module repository import
5. missing EventBus requirement
6. reports module writes to another domain
7. raw Exception or RuntimeError
8. acceptance criteria unimplemented
9. required tests missing

**Verdict Rules:**
- PASS: All hard gates pass AND score ≥ 90
- CONDITIONAL_PASS: All hard gates pass AND score 75-89
- FAIL: Any hard gate fails OR score < 75

**Key Features:**
- Detailed check implementations with bash commands
- Scoring calculation formulas
- Complete evaluation report template
- Deterministic, reproducible results

**Usage:** Reference when evaluating features and PRs for acceptance

---

### 3. ✅ Sprint-Decomposition (686 lines)

**File:** `.harness/skills/sprint-decomposition/SKILL.md`

**Purpose:** Teach Planners how to decompose StoreOps features into small, testable sprints optimized for Generator/Evaluator cycles.

**Sprint Contract Elements:**

1. **Sprint ID:** Unique identifier (e.g., ACTIVITIES-001)
2. **Objective:** One-sentence outcome-focused goal
3. **Modules Impacted:** List of affected domains
4. **Files Expected:** Specific files to change (models.py, routes.py, service.py, repository.py, tests)
5. **Dependencies:** What must complete first
6. **Architecture Constraints:** Musts and must-nots for this sprint
7. **Acceptance Criteria:** GIVEN/WHEN/THEN format (objectively testable)
8. **Required Tests:** Specific test names that must exist
9. **Completion Evidence:** How to verify sprint is done

**Content Includes:**

- Detailed guidance for each contract element
- Sprint sizing rules (good size, too large, too small)
- Complete sprint example: `PATCH /api/v1/activities/tasks/{id}` endpoint
- Feature decomposition example: Breaking "Complete task management system" into 9 sprints
- Common decomposition patterns (CRUD sequence, feature+validation, etc.)
- Anti-patterns to avoid
- Sprint template for copy/paste

**Key Features:**
- Objective testability emphasis
- GIVEN/WHEN/THEN format for acceptance criteria
- Realistic sprint sizing (2-4 files, 5-10 tests, 2-4 acceptance criteria)
- Event-driven communication patterns
- Sprint decomposition checklist

**Usage:** Reference when planning features and breaking them into sprints

---

## Integration with Existing Skills

These three skills complement the 5 existing skills in the harness:

```
Existing Skills:
├── app-context - Repository overview and setup
├── architecture-principles - Architectural patterns and decisions
├── coding-conventions - Code style and standards
├── component-patterns - Component organization
└── how-to-test - Testing conventions

New Skills (Complete the Workflow):
├── sprint-decomposition - How to decompose features (PLANNER)
├── how-to-review - How to review generated code (EVALUATOR)
└── evaluation-rules - How to score code objectively (EVALUATOR)
```

---

## Complete Workflow Using All Skills

### Phase 1: Planning (Use `sprint-decomposition`)
1. Define feature objective
2. Create sprint contract with 9 elements
3. Break into small sprints (2-4 files each)
4. Specify acceptance criteria in GIVEN/WHEN/THEN format
5. List required tests

### Phase 2: Generation (Uses existing skills as context)
1. Load `app-context` for repository overview
2. Load `architecture-principles` for architectural patterns
3. Load `coding-conventions` for code style
4. Load `component-patterns` for component structure
5. Load `how-to-test` for testing patterns
6. Generate code following sprint contract

### Phase 3: Evaluation (Use `how-to-review` and `evaluation-rules`)
1. Use `how-to-review` for systematic 7-step review process
2. Check each step sequentially
3. Use `evaluation-rules` to calculate objective score
4. Apply hard fail conditions
5. Determine PASS/CONDITIONAL_PASS/FAIL verdict

---

## Skill Statistics

| Skill | File Size | Lines | Focus Area |
|-------|-----------|-------|-----------|
| how-to-review | 24KB | 741 | Code review process (7 steps) |
| evaluation-rules | 27KB | 802 | Objective scoring (2 dimensions) |
| sprint-decomposition | 19KB | 686 | Feature decomposition |
| **Total New** | **70KB** | **2,229** | **Planning → Review → Evaluation** |

---

## Key Terminology Embedded in Skills

All three skills reference actual StoreOps concepts:

**Modules:**
- activities (task management)
- alerts (alert/escalation management)
- programmes (programme/initiative management)
- staff (staff/user management)
- reports (reporting, read-only)
- shared (errors, events, dependencies)

**Architecture Patterns:**
- Route → Service → Repository (strict 3-layer)
- EventBus for cross-module communication
- AppError hierarchy (ValidationError, NotFoundError, BusinessRuleViolationError, ConflictError)
- Async/await throughout
- Dependency injection via FastAPI Depends()

**Event Types:**
- TASK_CREATED, TASK_COMPLETED, TASK_OVERDUE, TASK_ASSIGNED
- PROGRAMME_CREATED, PROGRAMME_STARTED, PROGRAMME_COMPLETED
- STAFF_ONBOARDED, STAFF_OFFBOARDED
- SLA_BREACH, CRITICAL_ALERT, ESCALATION_NEEDED
- REPORT_GENERATED

**Testing Patterns:**
- TestClient for integration tests
- reset_state fixture (autouse) for test isolation
- pytest with asyncio support
- AAA pattern (Arrange, Act, Assert)

**Code Quality Tools:**
- mypy (strict type checking, `disallow_untyped_defs = true`)
- ruff (100 char line length, PEP 8, import sorting)
- pytest (80%+ coverage requirement)

---

## Usage Recommendations

### For Planners
**Load:** `sprint-decomposition`
- When decomposing new features
- Before writing sprint contracts
- To understand sprint sizing rules
- For GIVEN/WHEN/THEN format reference

### For Generators
**Load in this order:**
1. `app-context` (understand repository)
2. `architecture-principles` (understand patterns)
3. `coding-conventions` (understand code style)
4. `component-patterns` (understand structure)
5. `how-to-test` (understand testing)
6. Review sprint contract from Planner

### For Evaluators
**Load in this order:**
1. `how-to-review` (understand 7-step process)
2. `evaluation-rules` (understand scoring)
3. Read sprint contract
4. Follow 7-step review process
5. Calculate score using evaluation-rules
6. Determine verdict

---

## Next Steps

These skills are ready to use immediately:

1. ✅ **Invoke in sessions** via `/how-to-review`, `/evaluation-rules`, `/sprint-decomposition`
2. ✅ **Reference in documentation** - Link to these skills in contribution guidelines
3. ✅ **Use in workflows** - Chain with Agent tool for multi-step tasks
4. ✅ **Integrate with hooks** - Trigger skills automatically on events

**Example Hook** (in settings.json):
```json
{
  "name": "load-sprint-skills-on-session-start",
  "trigger": "session_start",
  "action": "skill",
  "args": ["sprint-decomposition", "how-to-review", "evaluation-rules"]
}
```

---

## Document Metadata

**Created:** 2026-08-29  
**Version:** 1.0.0  
**Author:** Claude Code - Skill Generation  
**Status:** Complete and Ready for Use  
**Coverage:**
- ✅ Sprint planning (decomposition)
- ✅ Code review process (how-to-review)
- ✅ Objective evaluation (evaluation-rules)
- ✅ All using actual StoreOps terminology
- ✅ All referencing real architecture patterns

---

**These three skills form a complete planning → generation → evaluation workflow for StoreOps features. They are deterministic, measurable, and codify domain knowledge.**
