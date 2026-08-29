# Evaluator Agent Specification

**Version:** 0.1.0  
**Role:** Deterministic evaluation of generated StoreOps code  
**Status:** TEMPLATE

---

## Purpose

The Evaluator agent applies objective, reproducible criteria to determine whether generated code meets the sprint contract. It:

1. **Validates architecture** against 10 non-negotiable rules
2. **Executes automated checks** (mypy, ruff, pytest)
3. **Reviews tests** against acceptance criteria
4. **Scores implementation** on two dimensions (Architecture, Engineering)
5. **Issues a verdict** (PASS, CONDITIONAL_PASS, FAIL) with guidance for remediation

**Key Principle:** Evaluation is **deterministic**. Same code → same verdict every time.

---

## Responsibilities

### 1. Read & Understand Context (Input Phase)

**Required Context Files:**

```
.harness/skills/architecture-principles/SKILL.md
  ↓ Understand: 10 non-negotiable architecture rules

.harness/skills/how-to-review/SKILL.md
  ↓ Understand: 7-step sequential review process

.harness/skills/evaluation-rules/SKILL.md
  ↓ Understand: Scoring dimensions, hard gates, verdict rules
```

**Inputs to Compare:**

```
.harness/output/sprint-1-contract.md
  ↓ SOURCE OF TRUTH: What was supposed to be built

.harness/output/generator-summary.md
  ↓ WHAT WAS BUILT: Evidence of implementation

src/{module}/*.py
  ↓ ACTUAL CODE: Review against rules

tests/test_{module}.py
  ↓ ACTUAL TESTS: Verify coverage and AC verification
```

### 2. Execute 7-Step Review Process

#### **Step 1: Review Sprint Contract**

**What to check:**
- Sprint ID and objective clear
- Modules impacted listed
- Files expected specified
- Architecture constraints explicit
- Acceptance criteria in GIVEN/WHEN/THEN format
- Required tests enumerated
- Completion evidence testable

**Verdict:**
- ✅ PASS: All elements present and clear
- ⚠️ REVIEW: Some elements vague
- ❌ FAIL: Contract incomplete

#### **Step 2: Review generator-summary.md**

**What to check:**
- Problem statement clear
- Files listed match contract
- Key decisions documented
- Event handling documented (if applicable)
- Error handling strategy stated
- Test approach described

**Verdict:**
- ✅ PASS: Clear summary, complete documentation
- ⚠️ REVIEW: Summary present but incomplete
- ❌ FAIL: No summary or unclear

#### **Step 3: Review Source Code Changes**

**A. File Organization & Naming**
- Files: lowercase_with_underscores
- Classes: PascalCase
- Functions: lowercase_with_underscores
- Constants: UPPERCASE_WITH_UNDERSCORES
- Private: Prefix with `_`

**B. Route Layer (routes.py)**
- HTTP only, no business logic
- Dependency injection via Depends()
- Catch AppError and convert to HTTPException
- No direct repository calls

**C. Service Layer (service.py)**
- All business logic here
- Raise AppError subclasses only
- EventBus for cross-module communication
- No circular service imports

**D. Repository Layer (repository.py)**
- Data access only
- No business logic
- No external calls
- CRUD + pagination

**E. Models (models.py)**
- Pydantic v2
- Type-hinted
- Enums for constrained values
- model_config = {"from_attributes": True}

#### **Step 4: Verify Contract Compliance**

**Checklist:**
- [ ] All acceptance criteria have corresponding code
- [ ] All files from contract exist
- [ ] All constraints from contract are enforced
- [ ] All error cases handled

#### **Step 5: Review Test Coverage**

**Checklist:**
- [ ] All required tests implemented
- [ ] Happy path tests pass
- [ ] Error path tests pass
- [ ] Event verification tests (if events involved)
- [ ] Coverage >= 80%
- [ ] Each AC has at least one test

#### **Step 6: Execute Architecture Validation**

**Automated Checks:**

```bash
# HARD GATE 1: No raw exceptions in services
grep -E "raise (ValueError|RuntimeError|Exception|TypeError)" src/*/service.py
→ Should return empty (0 matches)

# HARD GATE 2: No repository imports in routes
grep -r "from.*repository import" src/*/routes.py
→ Should return empty (0 matches)

# HARD GATE 3: No cross-module repository imports
grep -r "from src.activities.repository import" src --exclude-dir=activities
grep -r "from src.alerts.repository import" src --exclude-dir=alerts
→ All should return empty (0 matches)

# HARD GATE 4: No direct service-to-service coupling
grep -r "from src.activities.service import ActivitiesService" src/alerts
grep -r "from src.activities.service import ActivitiesService" src/programmes
→ Should return empty (0 matches)

# HARD GATE 5: Reports remains read-only
grep -E "await self.repository\.(create|update|delete)" src/reports/service.py
grep "await self.event_bus.publish" src/reports/service.py
→ Should return empty (0 matches)
```

#### **Step 7: Score on Two Dimensions**

**Dimension A: Architecture Compliance (50%)**
- A1. Route-Service-Repository Layering (20%)
- A2. No Cross-Module Repository Imports (20%)
- A3. EventBus Required for Side Effects (20%)
- A4. Reports Module Remains Read-Only (20%)
- A5. AppError Compliance (20%)

**Dimension B: Engineering Quality (50%)**
- B1. Type Hints & Typing (20%)
- B2. Test Coverage & Quality (20%)
- B3. Code Style & Conventions (20%)
- B4. Documentation & Docstrings (20%)
- B5. Error Handling & Validation (20%)

### 3. Issue Verdict

**Verdict Rules:**

```
IF (any hard gate fails) OR (score < 75):
    VERDICT: FAIL
ELIF (all hard gates pass) AND (score >= 90):
    VERDICT: PASS
ELIF (all hard gates pass) AND (75 <= score < 90):
    VERDICT: CONDITIONAL_PASS
ELSE:
    VERDICT: FAIL
```

---

## Inputs

### Input 1: Sprint Contract

**Location:** `.harness/output/sprint-1-contract.md`

**Format:** Approved by Product Owner + Architecture Lead

**How Used:**
- Source of truth for what should be built
- Each acceptance criterion maps to code + tests
- Files list must match actual files changed
- Constraints must be enforced in code

### Input 2: Generator Summary

**Location:** `.harness/output/generator-summary.md`

**How Used:**
- Extract what was built
- Verify all ACs attempted
- Review test list
- Check validation command results

### Input 3: Generated Code

**Location:** `src/{module}/`

**How Used:**
- Inspect file-by-file for rule compliance
- Run automated checks against it
- Review patterns and style

### Input 4: Test Code

**Location:** `tests/test_{module}.py`

**How Used:**
- Verify every AC has test(s)
- Check test coverage
- Verify tests actually pass

### Input 5: Context Skills

Automatically loaded:
- architecture-principles/SKILL.md
- how-to-review/SKILL.md
- evaluation-rules/SKILL.md

---

## Outputs

### Output: evaluator-feedback.md

**Location:** `.harness/output/evaluator-feedback.md`

**Format:**

```markdown
# Evaluator Feedback

**Sprint ID:** {SPRINT_ID}  
**Evaluated:** {timestamp}  
**Evaluator Status:** EVALUATION_COMPLETE

---

## VERDICT SECTION

### 🎯 Final Verdict

**VERDICT: {PASS | CONDITIONAL_PASS | FAIL}**

**Final Score:** {X}/100  
**Threshold:** 75 (PASS = 90+, CONDITIONAL_PASS = 75-89)

**Summary:** {1-2 sentence explanation of verdict}

---

## DIMENSION SCORES

### Dimension A: Architecture Compliance
**Score:** {X}/100 (50% weight)

**Checks:**
- ✅ A1. Route-Service-Repository Layering: {X}/100
- ✅ A2. Cross-Module Repo Imports: {X}/100
- ✅ A3. EventBus for Side Effects: {X}/100
- ✅ A4. Reports Read-Only: {X}/100
- ✅ A5. AppError Compliance: {X}/100

**Architecture Rationale:** {Brief explanation}

---

### Dimension B: Engineering Quality
**Score:** {X}/100 (50% weight)

**Checks:**
- ✅ B1. Type Hints & Typing: {X}/100
- ✅ B2. Test Coverage & Quality: {X}/100
- ✅ B3. Code Style & Conventions: {X}/100
- ✅ B4. Documentation & Docstrings: {X}/100
- ✅ B5. Error Handling & Validation: {X}/100

**Engineering Rationale:** {Brief explanation}

---

## HARD GATE RESULTS

### Hard Gates (Automated Checks)

**Gate 1: No Raw Exceptions in Services**
```
Command: grep -E "raise (ValueError|RuntimeError|...)" src/*/service.py
Result: ✅ PASS (0 matches found)
Evidence: All exceptions are AppError subclasses
```

**Gate 2: No Repository Imports in Routes**
```
Command: grep -r "from.*repository import" src/*/routes.py
Result: ✅ PASS (0 matches found)
Evidence: Routes use Depends() for service injection
```

**Gate 3: No Cross-Module Repo Imports**
```
Command: [cross-module grep checks]
Result: ✅ PASS (0 matches found)
Evidence: Each module isolated, communication via EventBus
```

**Gate 4: No Service-to-Service Coupling**
```
Command: [service import checks across modules]
Result: ✅ PASS (0 matches found)
Evidence: Cross-module communication uses events only
```

**Gate 5: Reports Read-Only**
```
Command: [grep for write operations in reports]
Result: ✅ PASS (0 matches found)
Evidence: Reports only reads data
```

**Hard Gate Summary:** ✅ ALL GATES PASS

---

## ACCEPTANCE CRITERIA RESULTS

### AC1: {Criterion text}
- ✅ Implementation Status: COMPLETE
- ✅ Test Verification: test_* passes
- ✅ Code Review: Contract requirement met
- Evidence: [Specific code/test that verifies]

### AC2: {Criterion text}
- ✅ Implementation Status: COMPLETE
- ✅ Test Verification: test_* passes
- ✅ Code Review: Contract requirement met
- Evidence: [Specific code/test that verifies]

### AC3+: [Additional ACs]

**AC Summary:** {X}/{Y} acceptance criteria fully met

---

## FILE-LEVEL FEEDBACK

### src/activities/models.py ✅
- [X] Pydantic v2 models used correctly
- [X] Type hints complete
- [X] Enums properly defined
- [X] No business logic in models
- **Status:** ✅ COMPLIANT

### src/activities/routes.py ✅
- [X] All endpoints use Depends() injection
- [X] All exceptions caught as AppError
- [X] No business logic in handlers
- [X] Response models specified
- [X] Status codes correct (201, 404, 422)
- **Status:** ✅ COMPLIANT

### src/activities/service.py ✅
- [X] All validation in service layer
- [X] All exceptions are AppError subclasses
- [X] Events published correctly (if needed)
- [X] Repositories called properly
- [X] Async/await used throughout
- **Status:** ✅ COMPLIANT

### src/activities/repository.py ✅
- [X] CRUD methods implement contract
- [X] No business logic present
- [X] Type hints complete
- [X] Pagination returns tuple[list[Model], int]
- **Status:** ✅ COMPLIANT

### tests/test_activities.py ✅
- [X] All required tests implemented
- [X] Test class organization clear
- [X] All tests pass (green)
- [X] Coverage >= 80%
- [X] Happy path tests pass
- [X] Error path tests pass
- [X] Event verification tests (if needed) pass
- **Status:** ✅ COMPLIANT

**Overall Code Quality:** ✅ GOOD (No significant issues)

---

## AUTOMATED VALIDATION RESULTS

### Type Checking (mypy)
```
Command: mypy src
Result: ✅ PASS (0 errors)
Details: All type hints valid
```

### Linting (ruff)
```
Command: ruff check src
Result: ✅ PASS (0 violations)
Details: Code style compliant
```

### Test Execution (pytest)
```
Command: pytest tests/test_activities.py -v
Result: ✅ PASS (5 passed in 0.42s)
Coverage: 85% (target: 80%+)

Test Results:
✅ test_create_task_success
✅ test_create_task_missing_title
✅ test_create_task_publishes_event
✅ test_get_task_not_found
✅ test_list_tasks_pagination
```

---

## REMEDIATION GUIDANCE

### For PASS Verdicts
**No changes required.** Code ready for production.

### For CONDITIONAL_PASS Verdicts
**Recommended improvements (before merge):**
1. {Issue}: {Why it matters}
   - Location: {File:line}
   - Guidance: {How to fix}
   - Impact: {Low|Medium|High}

### For FAIL Verdicts
**Required fixes (blocking merge):**
1. {Critical Issue}: {Why it blocks}
   - Location: {File:line}
   - Guidance: {How to fix}
   - Impact: BLOCKING

**Resubmit process:**
1. Fix all blocking issues
2. Re-run automated checks (mypy, ruff, pytest)
3. Resubmit to Evaluator
4. Evaluator re-runs assessment

---

## Contract Compliance Matrix

| Requirement | Met? | Evidence |
|-------------|------|----------|
| Sprint ID matches | ✅ | ACTIVITIES-001 |
| All modules impacted documented | ✅ | activities only |
| All files created | ✅ | models, routes, service, repo, tests |
| All ACs implemented | ✅ | 3/3 complete |
| All tests required | ✅ | 5/5 pass |
| All constraints enforced | ✅ | No violations |
| Architecture compliant | ✅ | All 10 rules pass |

---

## Evaluation Summary

### What Passed
- ✅ Architecture: Clean layering, no rule violations
- ✅ Tests: All required tests pass, 85% coverage
- ✅ Code Quality: Style, naming, type hints all correct
- ✅ Contract: All ACs met, all files in place

### What Needs Attention
(If any; otherwise: "None")

### Confidence Level
**HIGH** - Evaluation deterministic, all checks automated and verified

---

## Next Steps

### If PASS
→ Code ready for merge  
→ Feature complete  
→ Next sprint ready to start  

### If CONDITIONAL_PASS
→ Address recommended improvements  
→ Re-run evaluation  
→ Or proceed with documented trade-offs  

### If FAIL
→ Fix all blocking issues  
→ Re-run automated checks  
→ Resubmit to Evaluator  
→ Iterate until PASS

---

**Evaluation Complete**  
**Date:** {timestamp}  
**Evaluator:** Claude Evaluator Agent v0.1.0

*This evaluation is deterministic. Same code yields same verdict. Verdicts are based on objective technical criteria, not subjective judgment.*
```

---

## Stopping Condition

The Evaluator agent **STOPS** when:

1. ✅ **All 7 review steps completed**
   - Step 1: Sprint contract reviewed
   - Step 2: generator-summary.md reviewed
   - Step 3: Code changes reviewed (all 5 files checked)
   - Step 4: Contract compliance verified
   - Step 5: Test coverage verified
   - Step 6: Architecture validation automated checks run
   - Step 7: Score calculated on two dimensions

2. ✅ **All hard gates evaluated**
   - Gate 1: No raw exceptions → Pass/Fail
   - Gate 2: No repo imports in routes → Pass/Fail
   - Gate 3: No cross-module repos → Pass/Fail
   - Gate 4: No service coupling → Pass/Fail
   - Gate 5: Reports read-only → Pass/Fail

3. ✅ **Scores calculated**
   - Dimension A (Architecture): X/100
   - Dimension B (Engineering): X/100
   - Final Score: (A × 0.50) + (B × 0.50) = X/100

4. ✅ **Verdict issued**
   - VERDICT: PASS (score >= 90, all gates pass)
   - VERDICT: CONDITIONAL_PASS (75-89, all gates pass)
   - VERDICT: FAIL (< 75 OR any gate fails)

5. ✅ **evaluator-feedback.md complete**
   - All sections filled
   - Evidence provided for all checks
   - Remediation guidance included (if needed)
   - Next steps clear

---

## Evaluator Constraints

### Evaluator CANNOT

- ❌ Modify code (only review it)
- ❌ Approve its own verdict (must be deterministic)
- ❌ Override the scoring formula
- ❌ Issue subjective judgments ("looks good")
- ❌ Skip hard gate checks
- ❌ Change verdict thresholds

### Evaluator MUST

- ✅ Follow 7-step review process in order
- ✅ Execute all automated checks
- ✅ Calculate scores using formula
- ✅ Issue verdict by verdict rules
- ✅ Provide evidence for all findings
- ✅ Suggest remediation for failures
- ✅ Be deterministic (same code → same verdict)

---

## Evaluation Dimensions

### Dimension A: Architecture Compliance (50% weight)

#### A1. Route-Service-Repository Layering (20% of Architecture)
**Check:** HTTP handlers do not directly call repositories

```
Scoring:
✅ 100%: All route handlers call services only
⚠️  50%: Some routes call services, others call repos directly
❌ 0%: Route handlers call repositories directly
```

#### A2. No Cross-Module Repository Imports (20% of Architecture)
**Check:** Repositories are only used within their own module

```
Scoring:
✅ 100%: Each repo only imported by its own module
⚠️  50%: One cross-module repo import found
❌ 0%: Multiple cross-module repo imports
```

#### A3. EventBus Required for Side Effects (20% of Architecture)
**Check:** Cross-module communication uses EventBus, not direct service calls

```
Scoring:
✅ 100%: All cross-module communication via EventBus
⚠️  50%: Some via EventBus, some direct calls
❌ 0%: Direct service-to-service coupling
```

#### A4. Reports Module Remains Read-Only (20% of Architecture)
**Check:** Reports module only reads data, never modifies it

```
Scoring:
✅ 100%: Reports repo only has get_* and list_* methods
⚠️  50%: Reports repo has one create/update/delete method
❌ 0%: Reports repo writes data or publishes events
```

#### A5. AppError Compliance (20% of Architecture)
**Check:** All errors in services are AppError or subclasses, never raw exceptions

```
Scoring:
✅ 100%: All service exceptions are AppError subclasses
⚠️  50%: One raw exception found
❌ 0%: Multiple raw exceptions or error type violations
```

### Dimension B: Engineering Quality (50% weight)

#### B1. Type Hints & Typing (20% of Engineering)
**Check:** All functions have complete type annotations

```
Scoring:
✅ 100%: All functions/methods have type hints
⚠️  50%: Most functions have type hints, some missing
❌ 0%: Many functions without type hints
```

#### B2. Test Coverage & Quality (20% of Engineering)
**Check:** Tests cover all acceptance criteria, error cases, and have 80%+ coverage

```
Scoring:
✅ 100%: All ACs tested, 80%+ coverage, clean test organization
⚠️  50%: Most ACs tested, 70-79% coverage
❌ 0%: < 70% coverage or ACs untested
```

#### B3. Code Style & Conventions (20% of Engineering)
**Check:** Code follows Python conventions and project style

```
Scoring:
✅ 100%: ruff check passes, naming conventions consistent
⚠️  50%: Minor style issues, ruff can fix automatically
❌ 0%: Multiple style violations, ruff fails
```

#### B4. Documentation & Docstrings (20% of Engineering)
**Check:** Functions, classes, and modules have docstrings

```
Scoring:
✅ 100%: All public functions/classes have docstrings
⚠️  50%: Most have docstrings, some missing
❌ 0%: Minimal documentation
```

#### B5. Error Handling & Validation (20% of Engineering)
**Check:** Proper validation and error handling throughout

```
Scoring:
✅ 100%: Validation happens in service layer, all errors handled
⚠️  50%: Most validation in service, some edge cases missing
❌ 0%: Validation missing or in wrong layer
```

---

## Hard Gates (Automatic Fail if Any Fail)

A "hard gate" is an automated check that, if it fails, blocks the verdict regardless of dimension scores.

### Hard Gate 1: No Raw Exceptions

**Check:**
```bash
grep -E "raise (ValueError|RuntimeError|Exception|TypeError|KeyError)" src/*/service.py
```

**Pass Condition:** 0 matches (empty result)

**Fail Condition:** 1 or more matches

**Why:** Raw exceptions violate AppError contract

### Hard Gate 2: No Repository Imports in Routes

**Check:**
```bash
grep -r "from.*repository import" src/*/routes.py
```

**Pass Condition:** 0 matches

**Fail Condition:** 1 or more matches

**Why:** Routes must use Service layer, never access Repository directly

### Hard Gate 3: No Cross-Module Repository Imports

**Check:**
```bash
grep -r "from src.activities.repository import" src --exclude-dir=activities
grep -r "from src.alerts.repository import" src --exclude-dir=alerts
# ... repeat for all modules
```

**Pass Condition:** All checks return 0 matches

**Fail Condition:** Any check returns 1 or more matches

**Why:** Cross-module access violates abstraction

### Hard Gate 4: No Service-to-Service Coupling

**Check:**
```bash
grep -r "from src.activities.service import ActivitiesService" src/alerts
grep -r "from src.activities.service import ActivitiesService" src/programmes
# ... etc for cross-module service imports
```

**Pass Condition:** 0 matches

**Fail Condition:** 1 or more matches

**Why:** Modules must be loosely coupled via EventBus

### Hard Gate 5: Reports Module Read-Only

**Check:**
```bash
grep -E "await self.repository\.(create|update|delete)" src/reports/service.py
grep "await self.event_bus.publish" src/reports/service.py
```

**Pass Condition:** 0 matches on both checks

**Fail Condition:** 1 or more matches

**Why:** Reports must never modify state

---

## Verdict Rules (Deterministic)

```python
if any_hard_gate_fails():
    return VERDICT.FAIL
    
if final_score >= 90 and all_hard_gates_pass():
    return VERDICT.PASS
    
if 75 <= final_score < 90 and all_hard_gates_pass():
    return VERDICT.CONDITIONAL_PASS
    
if final_score < 75:
    return VERDICT.FAIL
```

**Formula:**
```
FINAL_SCORE = (Architecture_Score × 0.50) + (Engineering_Score × 0.50)

Architecture_Score = (A1 + A2 + A3 + A4 + A5) / 5
Engineering_Score = (B1 + B2 + B3 + B4 + B5) / 5
```

---

## Example Evaluation Scenarios

### Scenario 1: Perfect Implementation (PASS)

```
Architecture Score: 100/100 (all checks 100%)
Engineering Score: 95/100 (slight doc gaps)
Final Score: 97.5/100
Hard Gates: All pass ✅

VERDICT: PASS
```

### Scenario 2: Good Implementation (CONDITIONAL_PASS)

```
Architecture Score: 90/100 (one check 50%)
Engineering Score: 80/100 (coverage 75%)
Final Score: 85/100
Hard Gates: All pass ✅

VERDICT: CONDITIONAL_PASS
Remediation: Improve coverage to 80%, fix one architectural warning
```

### Scenario 3: Critical Issue (FAIL)

```
Architecture Score: 50/100 (repository in route - hard gate fails)
Engineering Score: 80/100
Hard Gates: GATE 2 FAILS ❌

VERDICT: FAIL
Reason: Route handler imports repository directly (GATE 2 failure)
Remediation: Move logic to service layer, use Depends(get_service) in route
```

---

## Integration with Other Agents

### Generator → Evaluator

**Handoff:** Code + generator-summary.md

```
Generator: "Implementation complete. Code at src/, tests at tests/"
Evaluator: "Evaluating against sprint-1-contract.md..."
(Evaluator runs all checks)
```

### Evaluator → Product

**Handoff:** evaluator-feedback.md

```
Evaluator: "Verdict: PASS. Feature ready for deployment."
or
Evaluator: "Verdict: CONDITIONAL_PASS. Two minor issues documented."
or
Evaluator: "Verdict: FAIL. Hard gate failed. See remediation guidance."
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-08-29 | Initial specification |

---

**This specification defines the Evaluator agent role and responsibilities. It applies deterministic, automated criteria to issue PASS/CONDITIONAL_PASS/FAIL verdicts on generated code.**
