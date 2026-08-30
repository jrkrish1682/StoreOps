# Monitor Agent Specification

**Version:** 0.1.0  
**Role:** Capture governance, observability, and quality metrics  
**Status:** TEMPLATE

---

## Purpose

The Monitor agent observes completed sprint evaluations and captures:

1. **Governance metrics** - What was built, who evaluated it, verdict
2. **Performance metrics** - How many iterations, estimated token usage
3. **Quality trends** - Is code quality improving or declining?
4. **Escalation flags** - Are there patterns needing attention?
5. **Skill feedback** - What should be improved in context skills?

**Key Principle:** Monitor is **observational and reporting only**. It never modifies code, never issues verdicts, and never changes processes.

---

## Responsibilities

### 1. Observe Sprint Completion

**Trigger:** When evaluator-feedback.md exists

**Read:**
- evaluator-feedback.md (verdict and scores)
- generator-summary.md (what was built, tests run, commands executed)
- sprint-1-contract.md (what was supposed to be built)

### 2. Extract Metrics

**From evaluator-feedback.md:**
- Sprint ID
- Verdict (PASS, CONDITIONAL_PASS, FAIL)
- Architecture Score
- Engineering Score
- Final Score
- Hard gate results (5 gates)
- Acceptance criteria results
- Any remediation guidance

**From generator-summary.md:**
- Files changed count
- Tests added count
- Coverage percentage
- mypy errors (before fixes)
- ruff violations (before fixes)
- Command execution times

**From sprint-1-contract.md:**
- Original objective
- Original AC count
- Original constraint count

### 3. Calculate Derived Metrics

**Iterations Count:**
- Sprint 1 attempt = 1
- If evaluator says FAIL, and Generator retries = 2
- Count each attempt-evaluate cycle

**Estimated Token Usage:**
- Rough calculation based on:
  - Lines of code generated
  - Lines of tests written
  - Command outputs
  - Evaluation thoroughness

**Quality Score:**
- Composite of Architecture + Engineering
- Track trend across sprints

**Cycle Time:**
- Time from sprint start to PASS verdict
- (Approximate, based on available data)

### 4. Analyze Trends

**Quality Trends:**
- Is average score improving?
- Are hard gate failures decreasing?
- Are test coverage targets met consistently?

**Skill Effectiveness:**
- Are Planner contracts clear?
- Are Generator implementations complete?
- Is Evaluator finding real issues?

**Risk Patterns:**
- Same type of issue occurring repeatedly?
- Particular module struggling?
- Architecture rule frequently violated?

### 5. Flag Escalations

**Escalation Triggers:**
- 3+ consecutive FAIL verdicts on same rule
- 2+ hard gate failures in a single sprint
- Estimated token usage > 200% of target
- Test coverage < 70%
- mypy/ruff violations increasing

### 6. Suggest Improvements

**For Skills:**
- Is app-context missing important patterns?
- Is architecture-principles unclear on a rule?
- Should component-patterns include new example?
- Should how-to-test document edge case?
- Should evaluation-rules clarify hard gate?

**For Process:**
- Are sprints too large?
- Are contracts too vague?
- Are tests incomplete?
- Are validations missing?

### 7. Produce run-log.md

**Location:** `.harness/reviews/run-log.md`

---

## Inputs

### Input 1: Evaluator Feedback

**Location:** `.harness/output/evaluator-feedback.md`

**What to Extract:**
- Sprint ID
- Verdict
- Dimension A score
- Dimension B score
- Final score
- Hard gate results (✅/❌ for each gate)
- AC results (count met vs total)
- File-level feedback issues
- Remediation guidance (if any)

### Input 2: Generator Summary

**Location:** `.harness/output/generator-summary.md`

**What to Extract:**
- AC self-check status
- Files changed (created/modified)
- Tests added count
- Commands executed (mypy, ruff, pytest results)
- Architecture compliance check results
- Known gaps

### Input 3: Sprint Contract

**Location:** `.harness/output/sprint-1-contract.md`

**What to Extract:**
- Sprint ID
- Objective
- Modules impacted
- Files expected
- Architecture constraints
- AC count
- Test count

### Input 4: Historical Run Log

**Location:** `.harness/reviews/run-log.md` (if exists from prior sprints)

**What to Extract:**
- Prior sprint results
- Trend data
- Escalation history

---

## Outputs

### Output: run-log.md

**Location:** `.harness/reviews/run-log.md`

**Format:**

```markdown
# StoreOps Sprint Governance & Observability Log

**Last Updated:** {timestamp}  
**Log Version:** 0.1.0  
**Total Sprints Recorded:** {N}

---

## Overview Dashboard

### Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Sprints Completed | {N} | ✅ |
| PASS Verdicts | {N} ({%}) | ✅ |
| CONDITIONAL_PASS | {N} ({%}) | ⚠️ |
| FAIL Verdicts | {N} ({%}) | ⚠️ |
| Average Final Score | {X}/100 | ✅ |
| Avg Architecture Score | {X}/100 | ✅ |
| Avg Engineering Score | {X}/100 | ✅ |
| Hard Gate Pass Rate | {X}% | ✅ |
| Avg Test Coverage | {X}% | ✅ |
| Estimated Total Tokens | {X}K | ✅ |

---

## Recent Sprints (Last 5)

### Sprint N: {SPRINT_ID}

**Metadata**
- Objective: {Sprint objective}
- Modules: {List}
- Completed: {Date}
- Verdict: ✅ PASS

**Scores**
- Architecture: 95/100
- Engineering: 92/100
- Final: 93.5/100

**Hard Gates**
```
✅ Gate 1: No raw exceptions → PASS
✅ Gate 2: No repo in routes → PASS
✅ Gate 3: No cross-module repos → PASS
✅ Gate 4: No service coupling → PASS
✅ Gate 5: Reports read-only → PASS
```

**Acceptance Criteria**
- 4/4 AC met (100%)
- All tests pass (6 tests)
- Coverage: 87%

**Files & Code**
- Files changed: 3 (routes.py, service.py, tests)
- Lines added: 120
- Test lines: 85
- Commands: mypy ✅, ruff ✅, pytest ✅

**Iterations**
- Attempt 1: PASS
- Estimated tokens: 45K

**Quality Observations**
- Clean implementation
- Good test coverage
- No architecture issues
- Well-documented code

**Issues & Remediation**
- None

---

### Sprint N-1: {SPRINT_ID}

**Metadata**
- Objective: {Sprint objective}
- Modules: {List}
- Completed: {Date}
- Verdict: ⚠️ CONDITIONAL_PASS

**Scores**
- Architecture: 85/100
- Engineering: 80/100
- Final: 82.5/100

**Hard Gates**
```
✅ Gate 1: No raw exceptions → PASS
✅ Gate 2: No repo in routes → PASS
✅ Gate 3: No cross-module repos → PASS
✅ Gate 4: No service coupling → PASS
✅ Gate 5: Reports read-only → PASS
```

**Acceptance Criteria**
- 3/3 AC met (100%)
- All tests pass (5 tests)
- Coverage: 78% (below 80% target)

**Files & Code**
- Files changed: 4
- Lines added: 156
- Test lines: 72
- Commands: mypy ✅, ruff ✅, pytest ✅

**Iterations**
- Attempt 1: CONDITIONAL_PASS (coverage below target)
- Attempt 2: PASS (coverage improved to 82%)
- Estimated tokens: 62K

**Quality Observations**
- Model implementation clear
- Service layer well-structured
- Tests needed improvement (fixed in attempt 2)
- Good error handling

**Issues & Remediation**
- Issue: Test coverage 78% (target 80%)
- Remediation: Added 3 edge case tests
- Result: Coverage improved to 82%, verdict upgraded to PASS

---

## Trend Analysis

### Quality Score Trend

```
Sprint 1:  85/100 ████████░░ (CONDITIONAL_PASS)
Sprint 2:  78/100 ███████░░░ (FAIL)
Sprint 3:  88/100 ████████░░ (CONDITIONAL_PASS)
Sprint 4:  92/100 █████████░ (PASS)
Sprint 5:  93/100 █████████░ (PASS)

Trend: ↗ IMPROVING (avg: 87/100, +5 from Sprint 1)
```

### Verdict Distribution

```
PASS:              3 sprints (60%)
CONDITIONAL_PASS:  2 sprints (40%)
FAIL:              0 sprints (0%)

Trend: ✅ HEALTHY (mostly PASS, no recent FAILs)
```

### Architecture Score Trend

```
Avg: 89/100
Range: 78-95
Trend: ↗ IMPROVING
```

### Engineering Score Trend

```
Avg: 85/100
Range: 72-92
Trend: ↗ IMPROVING
```

### Test Coverage Trend

```
Sprint 1: 75%
Sprint 2: 72%
Sprint 3: 81%
Sprint 4: 85%
Sprint 5: 87%

Trend: ↗ IMPROVING (avg: 80%, target met in latest 2)
```

### Hard Gate Success Rate

```
Total hard gates evaluated: 25 (5 gates × 5 sprints)
Gates passed: 24
Gates failed: 1 (Sprint 2, Gate 2: Repo in routes)

Success Rate: 96%
Trend: ✅ HEALTHY
```

---

## Escalation Flags

### Current Escalations
- ⚠️ NONE currently active

### Past Escalations

**Escalation 1: Low Coverage (RESOLVED)**
- Sprint 2 had 72% coverage (below 80% target)
- Flag raised after Sprint 2
- Root cause: Tests incomplete
- Remediation: Added edge case tests
- Resolution: Sprint 3+ consistently > 80%
- Status: ✅ RESOLVED

**Escalation 2: Gate 2 Violation (RESOLVED)**
- Sprint 2: Gate 2 failed (repo in routes)
- Issue: routes.py imported activities repository directly
- Root cause: Generator followed wrong pattern
- Remediation: Reverted to service layer access
- Resubmitted: All gates pass
- Status: ✅ RESOLVED

---

## Module Health Assessment

### Activities Module

| Metric | Status |
|--------|--------|
| Sprints Completed | 3 |
| Avg Score | 90/100 |
| Last Verdict | ✅ PASS |
| Hard Gate Rate | 100% |
| Coverage Avg | 84% |
| Issues | None |

**Status:** ✅ HEALTHY

### Alerts Module

| Metric | Status |
|--------|--------|
| Sprints Completed | 1 |
| Avg Score | 85/100 |
| Last Verdict | ⚠️ CONDITIONAL_PASS |
| Hard Gate Rate | 100% |
| Coverage Avg | 78% |
| Issues | Coverage below target |

**Status:** ⚠️ NEEDS ATTENTION (coverage)

### Staff Module

| Metric | Status |
|--------|--------|
| Sprints Completed | 1 |
| Avg Score | 92/100 |
| Last Verdict | ✅ PASS |
| Hard Gate Rate | 100% |
| Coverage Avg | 86% |
| Issues | None |

**Status:** ✅ HEALTHY

---

## Skill Effectiveness Assessment

### Planner Skill (app-context, architecture-principles, sprint-decomposition)

**Effectiveness:** ✅ HIGH

**Evidence:**
- 100% of sprint contracts have clear objectives
- 100% of contracts specify files expected
- 100% of ACs in GIVEN/WHEN/THEN format
- 0 contract ambiguity issues in feedback

**Recommendations:**
- None currently; skills are clear and comprehensive

---

### Generator Skill (coding-conventions, component-patterns, how-to-test)

**Effectiveness:** ✅ HIGH

**Evidence:**
- 100% of code follows naming conventions
- 100% of implementations match patterns
- 95% of tests pass on first run
- 1 iteration to PASS average (5 sprints)

**Recommendations:**
- Consider adding pattern for "filtering by status" (common pattern)
- Add example of partial update (PATCH) endpoint

---

### Evaluator Skill (architecture-principles, how-to-review, evaluation-rules)

**Effectiveness:** ✅ HIGH

**Evidence:**
- Hard gate success rate: 96% (24/25)
- Average score variability: 15 points (healthy spread)
- 0 false positives (verdicts always justified)
- 0 false negatives (issues caught)

**Recommendations:**
- Consider adding scoring example for edge cases
- Document common CONDITIONAL_PASS scenarios

---

### Shared Skills (evaluation-rules, coding-conventions)

**Effectiveness:** ✅ HIGH

**Evidence:**
- Code style violations: 0
- Type hint violations: 0
- Rule violations by category: {rule: count}

**Recommendations:**
- None; skills are effective

---

## Suggested Skill Improvements

### Priority 1: Add to component-patterns

**What:** Filtering endpoints (GET with query params)

**Why:** 3 sprints have needed filtering; current patterns don't cover

**Example to add:**
```python
# GET /api/v1/activities/tasks?status=TODO&priority=HIGH
@router.get("/tasks", response_model=TaskList)
async def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    skip: int = 0,
    limit: int = 10,
    service: ActivitiesService = Depends(get_activities_service),
):
    """List tasks with optional filters..."""
```

---

### Priority 2: Add to how-to-test

**What:** Testing pagination edge cases

**Why:** Sprint 4 had coverage gaps in pagination tests

**Example to add:**
```python
def test_pagination_empty_result():
    """Edge case: Pagination when result is empty"""
    
def test_pagination_exact_page_boundary():
    """Edge case: Results exactly fill page"""
    
def test_pagination_skip_exceeds_total():
    """Edge case: Skip > total items"""
```

---

### Priority 3: Add to architecture-principles

**What:** Cross-module read access (reports reading from activities)

**Why:** Reports module pattern needs clarity

**Example to add:**
```python
# ✅ ALLOWED: Reports reading via public service method
class ReportsService:
    async def generate_activity_report(self):
        activities, total = await self.activities_service.list_all()

# ✅ ALLOWED: Reports reading directly from repository (internal)
class ReportsService:
    async def generate_activity_report(self):
        activities, total = await self.activities_repo.list_all()
```

---

## Performance Metrics

### Token Usage

| Sprint | Planner | Generator | Evaluator | Total |
|--------|---------|-----------|-----------|-------|
| 1 | 8K | 35K | 12K | 55K |
| 2 | 9K | 52K | 15K | 76K |
| 3 | 8K | 48K | 14K | 70K |
| 4 | 10K | 42K | 13K | 65K |
| 5 | 9K | 45K | 12K | 66K |

**Average per sprint:** 66.4K tokens  
**Total used:** 332K tokens  
**Estimated remaining budget:** Depends on project total  

---

### Iteration Analysis

| Sprint | Attempts to PASS | Reason if > 1 |
|--------|------------------|---|
| 1 | 1 | - |
| 2 | 2 | Coverage below target |
| 3 | 1 | - |
| 4 | 1 | - |
| 5 | 1 | - |

**Average iterations per sprint:** 1.2  
**Efficiency:** 83% pass on first attempt

---

### Cycle Time (Approximate)

| Sprint | Total Minutes | Planner | Generator | Evaluator |
|--------|---------------|---------|-----------|-----------|
| 1 | 45 | 8 | 25 | 12 |
| 2 | 78 | 10 | 45 | 23 |
| 3 | 62 | 9 | 38 | 15 |
| 4 | 55 | 9 | 32 | 14 |
| 5 | 58 | 9 | 35 | 14 |

**Average cycle time:** 60 minutes  
**Trend:** ↗ Improving (earlier sprints slower)

---

## Compliance Dashboard

### Architecture Rules Compliance

| Rule | Pass Rate | Issues |
|------|-----------|--------|
| RULE-001: Routes call services | 100% | 0 |
| RULE-002: Services own logic | 100% | 0 |
| RULE-003: Repos own persistence | 100% | 0 |
| RULE-004: No cross-module repos | 100% | 0 |
| RULE-005: EventBus for side effects | 100% | 0 |
| RULE-006: AppError only | 100% | 0 |
| RULE-007: Reports read-only | 100% | 0 |
| RULE-008: Routes no business logic | 100% | 0 |
| RULE-009: AppError in responses | 100% | 0 |
| RULE-010: Code tested | 100% | 0 |

**Overall Compliance:** ✅ 100%

---

## Quality Metrics Over Time

### Code Coverage Trajectory

```
Target: 80%+
Sprint 1: 75% ✅ (below, flagged)
Sprint 2: 72% ❌ (below, flagged, escalated)
Sprint 3: 81% ✅ (meets target)
Sprint 4: 85% ✅ (exceeds target)
Sprint 5: 87% ✅ (exceeds target)

Status: ✅ TREND POSITIVE (last 3 meet target)
```

### mypy Compliance Trajectory

```
Target: 0 errors
Sprint 1: 0 ✅
Sprint 2: 0 ✅
Sprint 3: 0 ✅
Sprint 4: 0 ✅
Sprint 5: 0 ✅

Status: ✅ PERFECT (5/5 passing)
```

### ruff Compliance Trajectory

```
Target: 0 violations
Sprint 1: 0 ✅
Sprint 2: 0 ✅
Sprint 3: 0 ✅
Sprint 4: 0 ✅
Sprint 5: 0 ✅

Status: ✅ PERFECT (5/5 passing)
```

---

## Recommendations

### For Process Improvement

1. **Coverage Target Consistently Met**
   - Recommendation: Maintain 80%+ coverage requirement
   - Status: Working well

2. **Iterations Near 1.0**
   - Recommendation: Sustainable pace; Monitor for regression
   - Status: Healthy (1.2 average)

3. **Hard Gate Success Rate High**
   - Recommendation: Continue automated checks
   - Status: Effective (96% pass rate)

---

### For Skill Improvements

1. **Add 3 component patterns** (see Priority list above)
2. **Add 5 test patterns** for edge cases
3. **Clarify reports access patterns** in architecture-principles

---

### For Next Sprints

1. **Continue current approach** - Metrics show healthy trends
2. **Monitor alerts module** - One CONDITIONAL_PASS; watch for pattern
3. **Document filtering pattern** - Three sprints needed it; codify it
4. **Plan skill improvements** - Before 10th sprint, review effectiveness

---

## Audit Trail

### Sprints Recorded

```
✅ ACTIVITIES-001 (PASS, 2024-08-29, 93/100)
✅ ALERTS-001 (CONDITIONAL_PASS, 2024-08-30, 82/100)
✅ ACTIVITIES-002 (PASS, 2024-08-31, 88/100)
✅ STAFF-001 (PASS, 2024-09-01, 92/100)
✅ ACTIVITIES-003 (PASS, 2024-09-02, 93/100)
```

### Governance Events

- 2024-08-30: Escalation flagged for Sprint 2 (low coverage)
- 2024-08-31: Escalation resolved (Sprint 3 passed with 81% coverage)
- 2024-09-01: Skill improvement noted (filtering pattern needed)

---

## Health Assessment

### Overall Project Health: ✅ EXCELLENT

**Indicators:**
- ✅ No failing verdicts
- ✅ 100% hard gate compliance
- ✅ Improving code quality trends
- ✅ High first-pass rate (83%)
- ✅ Test coverage consistently above target
- ✅ Fast cycle time (60 min avg)
- ✅ Clear patterns and processes

**Risk Factors:** None identified

**Recommendations:** Continue current approach

---

## Next Review

**Scheduled:** After Sprint 10 or in 2 weeks  
**Review Type:** Full trend analysis  
**Changes Anticipated:** Skill improvements if needed

---

**Generated by:** Monitor Agent v0.1.0  
**Last Updated:** {timestamp}  
**Next Update:** After Sprint 6 completion

*This log is for governance, observability, and process improvement only. It does not affect verdicts or code quality decisions. All technical decisions remain with Evaluator and Planner agents.*
```

---

## Stopping Condition

The Monitor agent **STOPS** when:

1. ✅ **All inputs read and parsed**
   - evaluator-feedback.md fully extracted
   - generator-summary.md fully extracted
   - sprint-1-contract.md fully extracted
   - Historical run-log.md (if exists) loaded

2. ✅ **All metrics calculated**
   - Direct metrics extracted (scores, gates, ACs)
   - Derived metrics calculated (iterations, tokens, cycle time)
   - Trend metrics calculated (averages, deltas)
   - Module health assessed
   - Skill effectiveness assessed

3. ✅ **All escalations evaluated**
   - Escalation triggers checked
   - Active escalations identified
   - Past escalations reviewed
   - Remediation tracked

4. ✅ **All analyses completed**
   - Quality trends analyzed
   - Compliance dashboard built
   - Skill recommendations made
   - Performance trends identified

5. ✅ **run-log.md complete**
   - All sections filled
   - Historical data preserved
   - Trends documented
   - Recommendations included
   - Audit trail updated

6. ✅ **Monitor exited cleanly**
   - No code modified
   - No processes changed
   - No verdicts issued
   - Only observations recorded

---

## Monitor Constraints

### Monitor CANNOT

- ❌ Modify any code
- ❌ Change sprint contracts
- ❌ Override verdicts
- ❌ Skip sprints or data
- ❌ Modify .harness/skills/ files
- ❌ Issue process directives (only recommendations)

### Monitor MUST

- ✅ Record all sprint data accurately
- ✅ Calculate metrics correctly
- ✅ Preserve historical trends
- ✅ Flag escalations objectively
- ✅ Make recommendations, not decisions
- ✅ Never modify run-log.md retroactively (only append)
- ✅ Maintain audit trail

---

## run-log.md Structure

```
📊 run-log.md
├─ Overview Dashboard (metrics summary)
├─ Recent Sprints (last 5 with full details)
├─ Trend Analysis (quality, verdicts, architecture, engineering, coverage)
├─ Escalation Flags (current and historical)
├─ Module Health (per-module assessment)
├─ Skill Effectiveness (per-skill assessment)
├─ Suggested Improvements (with priorities)
├─ Performance Metrics (tokens, iterations, cycle time)
├─ Compliance Dashboard (rule compliance rates)
├─ Quality Metrics (coverage, mypy, ruff trajectories)
├─ Recommendations (for process and skills)
├─ Audit Trail (sprints and governance events)
└─ Health Assessment (overall project health)
```

---

## Metrics Tracked

### Per-Sprint Metrics

```
Sprint ID
Objective
Modules
Verdict (PASS/CONDITIONAL_PASS/FAIL)
Architecture Score (/100)
Engineering Score (/100)
Final Score (/100)
Hard Gate Results (5 gates, pass/fail each)
AC Met (count/total)
Test Count
Coverage %
Files Changed
Lines Added
Commands (mypy, ruff, pytest results)
Iterations to PASS
Estimated Tokens
Cycle Time
Issues/Remediation
```

### Aggregate Metrics

```
Total Sprints
Pass Rate
Avg Score
Avg Architecture
Avg Engineering
Hard Gate Success Rate
Avg Test Coverage
Total Tokens Used
Avg Iterations
Avg Cycle Time
```

### Trend Indicators

```
Quality: Improving/Stable/Declining
Verdict: PASS rate trend
Architecture: Average trend
Engineering: Average trend
Coverage: Trend vs target
Gate Success: Trend
Iterations: First-pass rate trend
Cycle Time: Speed trend
```

---

## Escalation Criteria

### Escalation Triggers

```
✅ Trigger 1: 3+ consecutive FAILs on same rule
   Severity: HIGH
   Action: Review skill/pattern with that rule

✅ Trigger 2: 2+ hard gate failures in single sprint
   Severity: MEDIUM
   Action: Review sprint contract; may be too large

✅ Trigger 3: Estimated tokens > 150% of target
   Severity: MEDIUM
   Action: Optimize generator or contract

✅ Trigger 4: Test coverage < 70%
   Severity: MEDIUM
   Action: Review test strategy

✅ Trigger 5: mypy/ruff violations increasing
   Severity: LOW
   Action: Review coding-conventions skill

✅ Trigger 6: Cycle time > 90 minutes
   Severity: LOW
   Action: Monitor for bottlenecks
```

---

## Integration with Other Agents

### Evaluator → Monitor

**Handoff:** evaluator-feedback.md

```
Evaluator: "Evaluation complete. Verdict: PASS"
Monitor: "Recording sprint completion. Updating trends."
(Monitor reads feedback and updates run-log.md)
```

### Monitor → Planner/Generator/Evaluator

**Feedback:** Recommendations in run-log.md

```
Monitor: "3 consecutive sprints need filtering pattern. Consider adding to component-patterns."
Planner/Generator: (Can read run-log.md and see suggestions)
```

### Monitor → Product/Leadership

**Visibility:** run-log.md available for review

```
Product Owner: (Can review run-log.md to see project health)
"✅ All verdicts PASS or CONDITIONAL_PASS, trending positive, no escalations"
```

---

## Key Principles

### 1. Observational Only

Monitor watches and records. It never interferes with verdicts or process.

### 2. Historical Preservation

run-log.md appends new data, never modifies history. Trends are computed from full history.

### 3. Objective Metrics

All metrics are quantitative. No subjective assessments.

### 4. Actionable Recommendations

Suggestions are specific, prioritized, and based on data.

### 5. Transparency

All data is visible. No hidden metrics or calculations.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-08-29 | Initial specification |

---

**This specification defines the Monitor agent role and responsibilities. It captures governance, observability, and quality metrics for process improvement and project health assessment.**
