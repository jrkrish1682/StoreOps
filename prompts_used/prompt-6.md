Read:

- docs/repository-assessment.md
- .harness/skills/app-context/SKILL.md
- .harness/skills/architecture-principles/SKILL.md
- Current StoreOps source code under src/
- Current tests under tests/

Create the following project-specific skill files:

1. .harness/skills/coding-conventions/SKILL.md
2. .harness/skills/component-patterns/SKILL.md
3. .harness/skills/how-to-test/SKILL.md

====================================================
CODING-CONVENTIONS SKILL
====================================================

Purpose:
Guide the Generator to produce code that matches the existing StoreOps codebase.

Document:

- Python typing standards
- FastAPI conventions
- Pydantic model patterns
- Import ordering
- Naming conventions
- Logging conventions
- Dependency injection approach
- Error handling approach
- AppError usage
- Repository usage
- Service layer practices
- EventBus usage patterns

For every rule include:

- Rule
- Example from repository
- Anti-pattern example

Only use conventions found in the actual repository.

====================================================
COMPONENT-PATTERNS SKILL
====================================================

Purpose:
Provide reusable implementation patterns for new features.

Document step-by-step patterns for:

1. Adding a new endpoint
2. Adding a service method
3. Adding repository operations
4. Creating request models
5. Creating response models
6. Raising AppError
7. Publishing EventBus events
8. Adding validation
9. Adding business rules
10. Implementing partial-failure handling

For each pattern show:

- Files affected
- Dependency direction
- Example implementation skeleton

Must follow:

Routes -> Service -> Repository

Cross-module side effects -> EventBus only

====================================================
HOW-TO-TEST SKILL
====================================================

Purpose:
Teach the Generator how StoreOps features are tested.

Document:

- Existing pytest structure
- Existing HTTPX usage
- Route testing pattern
- Service testing approach
- Happy path testing
- Error-path testing
- AppError testing
- EventBus testing
- Partial failure testing
- Acceptance criteria traceability

Explicitly state:

Testing only HTTP status codes is insufficient.

Every acceptance criterion must be validated by at least one test.

Document exact commands:

pytest
ruff check .
mypy src

Create practical examples using the existing StoreOps codebase.

====================================================

Output only the three skill files.

Do not create agent files yet.

Do not modify application code.