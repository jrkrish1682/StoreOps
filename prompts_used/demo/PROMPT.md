# Demonstration Feature Prompt

@planner Add Shift Handover Bulk Update capability.

## Requirements

- Add PATCH /api/activities/bulk-status.
- Update multiple activities in one request.
- Support partial success when some activity IDs are invalid or cannot be updated.
- Return item-level success and failure results.
- Create an audit entry for each successfully updated activity.
- Preserve StoreOps Route -> Service -> Repository layering.
- Do not access another module's repository directly.
- Use EventBus for cross-module side effects.
- Use the AppError hierarchy for request-level failures.
- Add automated tests covering the business rules and acceptance criteria.