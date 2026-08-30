# StoreOps Claude Code Development Harness

**Version:** 0.1.0  
**Status:** Active  
**Last Updated:** 2026-08-29  

---

## Overview

This file defines the **operational flow** for developing StoreOps features using Claude Code agents. The harness automates feature specification, implementation, evaluation, and governance—transforming unstructured feature requests into production-ready, architecture-compliant code.

**Key Principle:** Human-driven approval gates + deterministic, reproducible agent workflows = high confidence in shipped code.

---

## ⚡ Quick Start: Developer Invocation

To start a new feature:

```
@planner <feature request>
```

**Example:**
```
@planner Add bulk task status update API so managers can rapidly transition multiple tasks through workflow states with a single request
```

The harness then follows a multi-phase workflow. **Keep reading for the full process.**

---

## 📋 Workflow Phases

### Phase 1: PLANNER (Specification)

**Agent:** `planner.agent.md`  
**Input:** Your feature request (natural language)  
**Duration:** 5-15 minutes  
**Output:** Specification + Sprint 1 contract

#### What the Planner Does

1. **Reads context** from `.harness/skills/`:
   - `app-context/SKILL.md` — Understands StoreOps module structure
   - `architecture-principles/SKILL.md` — Learns 10 non-negotiable rules
   - `sprint-decomposition/SKILL.md` — Knows how to break work into sprints

2. **Analyzes your feature request:**
   - Extracts business intent
   - Maps to affected modules
   - Identifies data models, endpoints, events, errors
   - Validates against architecture rules

3. **Produces two artifacts:**

   **→ `.harness/output/spec.md`**
   - High-level analysis
   - Module impact
   - API endpoints
   - Events, errors, constraints
   - Sprint decomposition
   - All 10 rules evaluated
   - **Status:** `AWAITING_APPROVAL`

   **→ `.harness/output/sprint-1-contract.md`**
   - Concrete, testable Sprint 1 contract
   - Sprint ID, objective, files expected
   - Acceptance criteria in GIVEN/WHEN/THEN format
   - Required tests enumerated
   - Architecture constraints listed
   - **Status:** `AWAITING_APPROVAL`

#### What Planner Does NOT Do

- ❌ Write any application code
- ❌ Run tests
- ❌ Approve its own work
- ❌ Skip rule validation

#### Planner Stops When

✅ Both `spec.md` and `sprint-1-contract.md` are complete  
✅ All 10 architecture rules evaluated  
✅ STATUS fields set to `AWAITING_APPROVAL`

---

### Phase 2: APPROVAL (Human Decision Gate)

**Participants:** Product Owner + Architecture Lead  
**Input:** `spec.md` + `sprint-1-contract.md`  
**Duration:** 15-30 minutes  
**Decision:** APPROVED or CHANGES_REQUESTED

#### Product Owner Review

- [ ] Feature addresses stated business problem?
- [ ] Acceptance criteria clear and measurable?
- [ ] Success metrics verifiable?
- [ ] Any scope missing from Sprint 1?

#### Architecture Lead Review

- [ ] All 10 rules evaluated as compliant?
- [ ] Dependencies realistic?
- [ ] Sprint 1 scope appropriate?
- [ ] Test strategy sound?
- [ ] Error handling complete?

#### Approval Process

**If APPROVED:**
```
Developer: APPROVED
→ Proceeds to Phase 3: EXECUTION
```

**If Changes Requested:**
```
Reviewer: [Issue description]
→ Planner revises affected section(s)
→ Resubmit for re-approval (mark as REVISION_1, REVISION_2, etc.)
```

**If Rejected:**
```
Reviewer: [Rejection reason]
→ STOP: Restart with new feature request
```

---

### Phase 3: EXECUTION (Implement, Evaluate, Iterate)

For each approved sprint, run this loop:

#### Attempt N (Generator + Evaluator cycle)

**Step 1: Run Generator**

```
Generator agent processes: sprint-1-contract.md
```

**Generator reads context:**
- `app-context/SKILL.md` — Application structure
- `architecture-principles/SKILL.md` — Governance rules
- `coding-conventions/SKILL.md` — Python style
- `component-patterns/SKILL.md` — Code patterns
- `how-to-test/SKILL.md` — Test patterns

**Generator produces:**
- ✅ Implementation code in `src/{module}/`
- ✅ Test code in `tests/`
- ✅ `.harness/output/generator-summary.md` (evidence of build)

**Generator validates:**
```bash
mypy src           # Type checking → must pass
ruff check src     # Linting → must pass
ruff format src    # Auto-format
pytest tests/      # All tests → must pass
```

**Step 2: Run Evaluator**

```
Evaluator agent processes: sprint-1-contract.md + generated code + generator-summary.md
```

**Evaluator reads context:**
- `architecture-principles/SKILL.md` — 10 rules to validate
- `how-to-review/SKILL.md` — 7-step review process
- `evaluation-rules/SKILL.md` — Scoring criteria

**Evaluator performs 7-step review:**
1. Review sprint contract (clear? specific? testable?)
2. Review generator-summary.md (complete? accurate?)
3. Review source code changes (patterns? style? layering?)
4. Verify contract compliance (all files? all ACs?)
5. Review test coverage (80%+? all ACs tested?)
6. Execute architecture validation (hard gates)
7. Score on two dimensions & issue verdict

**Hard Gates (Automatic Fail if Any Fail):**
- ✅ Gate 1: No raw exceptions in services
- ✅ Gate 2: No repository imports in routes
- ✅ Gate 3: No cross-module repository imports
- ✅ Gate 4: No direct service-to-service coupling
- ✅ Gate 5: Reports module remains read-only

**Scoring Dimensions:**
- **Dimension A (Architecture Compliance):** 50%
  - A1. Route-Service-Repository Layering (20%)
  - A2. No Cross-Module Repo Imports (20%)
  - A3. EventBus for Side Effects (20%)
  - A4. Reports Module Read-Only (20%)
  - A5. AppError Compliance (20%)

- **Dimension B (Engineering Quality):** 50%
  - B1. Type Hints & Typing (20%)
  - B2. Test Coverage & Quality (20%)
  - B3. Code Style & Conventions (20%)
  - B4. Documentation & Docstrings (20%)
  - B5. Error Handling & Validation (20%)

**Evaluator produces:**
- ✅ `.harness/output/evaluator-feedback.md` (verdict + evidence)

---

## 🎯 Verdict Routing

After Evaluator issues verdict, route as follows:

### VERDICT: PASS (Score ≥ 90, all gates pass)

```
✅ PASS → Code ready for merge

Actions:
1. Execute Monitor (record metrics)
2. Archive sprint artifacts to .harness/reviews/
3. Continue to next sprint (if any)
```

### VERDICT: CONDITIONAL_PASS (Score 75-89, all gates pass)

```
⚠️ CONDITIONAL_PASS → Minor issues, ready after remediation

Actions:
1. Review "Remediation Guidance" section in evaluator-feedback.md
2. Generator fixes recommended issues (unless documentation-only)
3. Resubmit to Evaluator (= Attempt 2)
4. If still CONDITIONAL_PASS after fixes, OR all issues are documentation:
   → Proceed to Monitor & next sprint
   → Or choose to re-attempt (up to 3 total attempts)
```

### VERDICT: FAIL (Score < 75, OR any gate fails)

```
❌ FAIL → Blocking issues, retry required

Actions:
1. Review "Required Fixes" section in evaluator-feedback.md
2. Generator addresses all blocking issues
3. Resubmit to Evaluator (= Attempt 2)
4. Repeat until PASS or CONDITIONAL_PASS
```

---

## 🔄 Iteration Limits

**Maximum attempts per sprint:** 3 (Generator/Evaluator cycles)

**After 3rd unsuccessful attempt:**

1. Create `.harness/output/escalation.md` with:
   - Sprint ID
   - Iteration count (3)
   - Failed checks (from all 3 evaluations)
   - Hard gate violations (if any)
   - Blocking issues (summarized)
   - Files affected
   - Recommended developer action

2. **STOP** harness execution

3. Developer reviews escalation and decides:
   - Revise feature request scope
   - Request architectural guidance
   - Postpone sprint
   - Restart with different approach

---

## 📊 Monitor Phase

**Trigger:** After PASS or CONDITIONAL_PASS verdict

**Agent:** `monitor.agent.md`  
**Input:** evaluator-feedback.md + generator-summary.md + sprint-1-contract.md  
**Duration:** 5-10 minutes  
**Output:** `.harness/reviews/run-log.md`

### What Monitor Does

1. **Extracts metrics** from sprint evaluation:
   - Sprint ID, verdict, scores
   - Architecture/Engineering dimensions
   - Hard gate results
   - Test coverage, AC completion
   - Iteration count, estimated token usage

2. **Analyzes trends:**
   - Quality improving/stable/declining?
   - Test coverage consistent?
   - Architecture compliance rate?
   - Cycle time?

3. **Flags escalations** (if any):
   - 3+ consecutive FAILs on same rule
   - 2+ hard gate failures in single sprint
   - Test coverage < 70%
   - Token usage > 150% of target

4. **Suggests improvements:**
   - Skills needing clarification
   - Patterns needing documentation
   - Process optimizations

5. **Updates run-log.md:**
   - Overview dashboard (metrics summary)
   - Recent sprints (detailed records)
   - Trend analysis (quality, verdicts, coverage)
   - Escalation flags
   - Module health assessment
   - Skill effectiveness assessment
   - Recommendations

---

## 📁 Archive Strategy

After each sprint completes (PASS or CONDITIONAL_PASS), archive evidence:

```
.harness/reviews/
├── {SPRINT_ID}.md          # Sprint record (copied from output/)
│   ├── spec.md
│   ├── sprint-1-contract.md
│   ├── generator-summary.md
│   ├── evaluator-feedback.md
│   └── run-log.md (appended to run-log.md)
```

**Purpose:** Maintain audit trail + historical trends

---

## 🏗️ Context Management

### Context Resets Between Sprints

Each agent receives a fresh context package:

**Planner receives:**
- `app-context/SKILL.md`
- `architecture-principles/SKILL.md`
- `sprint-decomposition/SKILL.md`

**Generator receives:**
- `app-context/SKILL.md`
- `architecture-principles/SKILL.md`
- `coding-conventions/SKILL.md`
- `component-patterns/SKILL.md`
- `how-to-test/SKILL.md`
- `sprint-1-contract.md` (from .harness/output/)
- `spec.md` (for reference)

**Evaluator receives:**
- `architecture-principles/SKILL.md`
- `how-to-review/SKILL.md`
- `evaluation-rules/SKILL.md`
- `sprint-1-contract.md` (source of truth)
- `generator-summary.md` (what was built)
- Generated code in `src/` and `tests/`

**Monitor receives:**
- `evaluator-feedback.md` (verdict + scores)
- `generator-summary.md` (what was built)
- `sprint-1-contract.md` (what was supposed to be built)
- `run-log.md` (historical data, if exists)

### Handoff Files as Source of Truth

Agents communicate via files in `.harness/output/`:

```
.harness/output/
├── spec.md                 ← Planner → Evaluator (reference)
├── sprint-1-contract.md    ← Planner → Generator → Evaluator (primary)
├── generator-summary.md    ← Generator → Evaluator → Monitor
├── evaluator-feedback.md   ← Evaluator → Monitor → Archive
└── escalation.md           ← Generated if 3 attempts fail
```

Each file is the source of truth for the next agent's inputs.

---

## 🚀 CI/CD Strategy

### Harness is Pre-Pipeline Validation

The harness validates **before** committing to CI/CD:

```
Feature Request
    ↓
Planner → spec.md + sprint-1-contract.md (AWAITING_APPROVAL)
    ↓
[Human: APPROVED / CHANGES_REQUESTED]
    ↓
Generator → implementation code + tests (GENERATION_COMPLETE)
    ↓
Evaluator → verdict (PASS/CONDITIONAL_PASS/FAIL)
    ↓
[If PASS or CONDITIONAL_PASS: Merge to main]
    ↓
CI/CD Pipeline (Additional validation, build, deploy)
```

### Harness ≠ CI/CD Replacement

- ✅ Harness validates against **architecture rules** + **patterns**
- ✅ CI/CD validates against **deployment requirements** + **infrastructure**
- ✅ Both are necessary; harness runs **first**

### Why This Order?

1. **Fail fast on architecture issues** (cheaper to fix before CI)
2. **Deterministic feedback** (harness verdict is reproducible)
3. **Human approval gate** (before resource-intensive CI)
4. **Audit trail** (harness records all decisions)

---

## 📝 File Organization

```
.harness/
├── agents/                          # Agent specifications
│   ├── planner.agent.md
│   ├── generator.agent.md
│   ├── evaluator.agent.md
│   └── monitor.agent.md
│
├── skills/                          # Context for agents
│   ├── app-context/SKILL.md         # Module structure
│   ├── architecture-principles/SKILL.md    # 10 rules
│   ├── coding-conventions/SKILL.md  # Python style
│   ├── component-patterns/SKILL.md  # Code templates
│   ├── evaluation-rules/SKILL.md    # Scoring criteria
│   ├── how-to-review/SKILL.md       # Review process
│   ├── how-to-test/SKILL.md         # Test patterns
│   └── sprint-decomposition/SKILL.md # Sprint sizing
│
├── output/                          # Working directory (current sprint)
│   ├── spec.md
│   ├── sprint-1-contract.md
│   ├── generator-summary.md
│   ├── evaluator-feedback.md
│   └── escalation.md                # If 3 attempts fail
│
└── reviews/                         # Archive (historical sprints)
    ├── run-log.md                   # Cumulative metrics & trends
    └── {SPRINT_ID}.md               # Per-sprint records
```

---

## 🎓 Typical Workflow Example

### User Request

```
@planner Add bulk task status update API
```

### Planner Output (15 min)

```
✅ .harness/output/spec.md (AWAITING_APPROVAL)
   - Feature overview
   - Business problem: Managers need to transition multiple tasks at once
   - Modules impacted: activities only
   - Endpoints: PATCH /api/v1/activities/tasks/bulk with IDs + new status
   - Events: TASK_UPDATED (per task)
   - Errors: VALIDATION_ERROR, NOT_FOUND
   - Sprint 1 size: 3 files, 8 tests, 2 AC

✅ .harness/output/sprint-1-contract.md (AWAITING_APPROVAL)
   - Sprint ID: ACTIVITIES-002
   - Objective: Bulk update tasks to new status with validation
   - AC1: Update 5 tasks to DONE in one request
   - AC2: Validate all tasks exist before any updates
   - AC3: Publish TASK_UPDATED event per task
```

### Approval (20 min)

```
Product Owner: "Spec looks good. AC clear. Approve."
Architecture Lead: "All rules compliant. Constraints achievable. Approve."
Developer: APPROVED
```

### Generator (30 min)

```
✅ Generated code:
   - src/activities/models.py: Added BulkUpdateRequest
   - src/activities/routes.py: Added PATCH /tasks/bulk
   - src/activities/service.py: Added update_tasks_bulk()
   - tests/test_activities.py: Added 8 tests
   
✅ Validation:
   - mypy: 0 errors
   - ruff: 0 violations
   - pytest: 8/8 pass, 87% coverage
   
✅ .harness/output/generator-summary.md (GENERATION_COMPLETE)
   - All ACs implemented
   - All tests pass
   - All commands pass
```

### Evaluator (15 min)

```
✅ Review sprint contract
✅ Review generator summary
✅ Review code changes (all patterns match)
✅ Verify contract compliance (all ACs verified by tests)
✅ Review test coverage (87% ≥ 80%)
✅ Execute hard gates (all 5 pass)
✅ Score:
   - Architecture: 95/100
   - Engineering: 92/100
   - Final: 93.5/100

✅ VERDICT: PASS

.harness/output/evaluator-feedback.md (EVALUATION_COMPLETE)
```

### Monitor (10 min)

```
✅ Extract metrics
✅ Update .harness/reviews/run-log.md:
   - ACTIVITIES-002: PASS, 93/100, 1 attempt, 45K tokens
   - Trend: Quality improving (ACTIVITIES: avg 90/100)
   - Hard gates: 5/5 pass
   - Recommendations: None

✅ Code ready for merge
```

### Result

```
✅ Code merged to main
✅ CI/CD pipeline runs additional validation
✅ Feature deployed
✅ Audit trail in run-log.md
```

---

## 🚨 Troubleshooting

### Generator Fails (Attempt 1 → FAIL)

**Check evaluator-feedback.md → "Required Fixes"**

Example issues:
- ❌ Route directly calls repository (RULE-001 violation) → Move to service
- ❌ Service raises ValueError (not AppError) → Wrap in AppError
- ❌ Test coverage 73% (below 80%) → Add edge case tests

**Fix and retry:** Generator re-runs with corrected contract or code

### Conditional_Pass (Score 75-89)

**Check evaluator-feedback.md → "Recommended Improvements"**

Examples:
- ⚠️ Coverage 76% (just below target) → Add 2-3 tests
- ⚠️ Documentation incomplete → Add docstrings
- ⚠️ Error messages unclear → Improve error text

**Choose:** Retry to PASS, or accept and merge if business value high

### 3 Attempts Exhausted

**Check escalation.md**

This means:
- Sprint contract may be too vague
- Feature scope may be too large
- Architecture may need re-review

**Developer action:**
- Revise feature request for clarity
- Reduce scope to smaller sprint
- Request architecture guidance

---

## 🔐 Process Guarantees

✅ **Deterministic:** Same feature request → same code → same verdict (always)

✅ **Reproducible:** Every step is recorded in `.harness/output/` + `.harness/reviews/`

✅ **Auditable:** Full trace of planner decisions, generator code, evaluator scoring

✅ **Approvable:** Human gates at specification stage + approval stage

✅ **Measurable:** Metrics tracked in run-log.md (scores, coverage, iterations, trends)

✅ **Architectural:** All 10 rules enforced by hard gates + evaluator

✅ **Testable:** 80%+ coverage required; all acceptance criteria verified by tests

---

## 📞 Support & Questions

### About the Harness Process?

→ Read this file (CLAUDE.md)

### About Planning a Feature?

→ Review `.harness/skills/sprint-decomposition/SKILL.md`

### About Architecture Rules?

→ Review `.harness/skills/architecture-principles/SKILL.md`

### About Code Patterns?

→ Review `.harness/skills/component-patterns/SKILL.md`

### About Evaluation Criteria?

→ Review `.harness/skills/evaluation-rules/SKILL.md`

### About Metrics & Trends?

→ Review `.harness/reviews/run-log.md`

---

## 🗂️ Agent Reference

| Agent | Role | Input | Output | Duration |
|-------|------|-------|--------|----------|
| **Planner** | Specification | Feature request | spec.md + sprint-1-contract.md | 5-15 min |
| **Generator** | Implementation | sprint-1-contract.md | Code + tests + generator-summary.md | 20-45 min |
| **Evaluator** | Quality gate | Code + generator-summary.md | evaluator-feedback.md + VERDICT | 10-20 min |
| **Monitor** | Governance | Evaluator feedback | run-log.md (updated) | 5-10 min |

---

## 📜 Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-08-29 | Initial specification |

---

## ✅ Checklist: Before Invoking Harness

- [ ] Feature request is clear and focused (not vague)
- [ ] Business outcome is stated (not just "add X endpoint")
- [ ] Success metrics are measurable
- [ ] No architectural red flags (cross-module tightly coupled, etc.)
- [ ] `.harness/output/` is clean (no stale files from prior sprints)

---

**This is the operational guide for the StoreOps Claude Code Development Harness. Follow the phases, respect the verdict routing, and trust the deterministic process.**

🚀 **Ready to build something great with Claude.**
