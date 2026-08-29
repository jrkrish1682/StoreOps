"""
Service layer for Activities module.

Responsibilities:
- Business logic
- Validation
- Orchestration
- Publishing events
- Always raise AppError (never raw exceptions)
- Call repositories only
- May read from other modules' services
"""

from datetime import UTC, datetime
from typing import Any, ClassVar

from src.activities.models import (
    BulkActivityStatusUpdateResult,
    BulkUpdateFailedItem,
    BulkUpdateSummary,
    Task,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
)
from src.activities.repository import ActivitiesRepository, get_activities_repository
from src.shared.errors import (
    ErrorCode,
    NotFoundError,
    ValidationError,
)
from src.shared.event_bus import EventBus, EventType


class ActivitiesService:
    """Service for managing activities/tasks."""

    # Valid status transitions
    VALID_TRANSITIONS: ClassVar[dict[str, list[str]]] = {
        TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED],
        TaskStatus.IN_PROGRESS: [TaskStatus.DONE, TaskStatus.BLOCKED],
        TaskStatus.DONE: [],  # Terminal state
        TaskStatus.BLOCKED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
    }

    def __init__(
        self,
        repository: ActivitiesRepository,
        event_bus: EventBus,
    ) -> None:
        """Initialize service.

        Args:
            repository: Activities repository
            event_bus: Event bus for publishing events
        """
        self.repository = repository
        self.event_bus = event_bus

    def _is_valid_transition(
        self,
        current_status: str,
        new_status: str,
    ) -> bool:
        """Check if transition is valid.

        Args:
            current_status: Current status
            new_status: Desired status

        Returns:
            True if transition is allowed
        """
        if current_status == new_status:
            return False  # No change is not a valid transition
        return new_status in self.VALID_TRANSITIONS.get(current_status, [])

    async def create_task(
        self,
        task_create: TaskCreate,
        current_user_id: str | None = None,
    ) -> Task:
        """Create new task with validation.

        Args:
            task_create: Task creation data
            current_user_id: User creating the task

        Returns:
            Created task

        Raises:
            ValidationError: If validation fails
        """
        # Validation
        if not task_create.title or not task_create.title.strip():
            raise ValidationError(
                message="Task title is required",
            )

        # Create task
        task = await self.repository.create(
            task_create=task_create,
            created_by=current_user_id,
        )

        # Publish event
        await self.event_bus.publish(
            EventType.TASK_CREATED,
            {
                "task_id": task.id,
                "title": task.title,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        )

        return task

    async def get_task(self, task_id: str) -> Task:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task

        Raises:
            NotFoundError: If task not found
        """
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundError(resource_type="Task", resource_id=task_id)
        return task

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> dict[str, Any]:
        """List tasks with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Dict with tasks and pagination info
        """
        tasks, total = await self.repository.list_all(skip=skip, limit=limit)
        return {
            "items": tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_task(
        self,
        task_id: str,
        task_update: TaskUpdate,
    ) -> Task:
        """Update task.

        Args:
            task_id: Task ID
            task_update: Update data

        Returns:
            Updated task

        Raises:
            NotFoundError: If task not found
            ValidationError: If validation fails
        """
        # Get existing task
        existing = await self.repository.get_by_id(task_id)
        if not existing:
            raise NotFoundError(resource_type="Task", resource_id=task_id)

        # Validate update
        if task_update.title is not None:
            if not task_update.title or not task_update.title.strip():
                raise ValidationError(message="Task title cannot be empty")

        # Update task
        updated_task = await self.repository.update(task_id, task_update)
        if not updated_task:
            raise NotFoundError(resource_type="Task", resource_id=task_id)

        # Publish event if status changed
        if (
            task_update.status
            and task_update.status != existing.status
            and task_update.status == TaskStatus.DONE
        ):
            await self.event_bus.publish(
                EventType.TASK_COMPLETED,
                {
                    "task_id": task_id,
                    "title": updated_task.title,
                    "completed_at": updated_task.updated_at.isoformat(),
                },
            )

        return updated_task

    async def delete_task(self, task_id: str) -> bool:
        """Delete task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted

        Raises:
            NotFoundError: If task not found
        """
        deleted = await self.repository.delete(task_id)
        if not deleted:
            raise NotFoundError(resource_type="Task", resource_id=task_id)
        return True

    async def get_tasks_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 10,
    ) -> dict[str, object]:
        """Get tasks filtered by status.

        Args:
            status: Task status
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Dict with tasks and pagination info
        """
        tasks, total = await self.repository.list_by_status(
            status=status,
            skip=skip,
            limit=limit,
        )
        return {
            "items": tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_user_tasks(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> dict[str, object]:
        """Get tasks assigned to user.

        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Dict with tasks and pagination info
        """
        tasks, total = await self.repository.list_by_assigned_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
        return {
            "items": tasks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def bulk_update_activities(
        self,
        activity_ids: list[str],
        new_status: str,
        current_user_id: str | None = None,
    ) -> BulkActivityStatusUpdateResult:
        """Update status for multiple activities.

        Args:
            activity_ids: List of activity IDs
            new_status: New status to set (as string, will be validated)
            current_user_id: User performing the update

        Returns:
            BulkActivityStatusUpdateResult with succeeded/failed items

        Raises:
            ValidationError: If request-level validation fails
        """
        # Phase 1: Request-level validation

        # Validate activity_ids not empty
        if not activity_ids:
            raise ValidationError(
                message="activity_ids is required and must not be empty",
                details={"field": "activity_ids"},
            )

        # Validate activity_ids length <= 100
        if len(activity_ids) > 100:
            raise ValidationError(
                message="activity_ids must contain at most 100 items",
                details={"field": "activity_ids"},
            )

        # Validate status enum
        try:
            validated_status = TaskStatus(new_status)
        except ValueError:
            raise ValidationError(
                message=f"new_status '{new_status}' is not a valid TaskStatus",
                details={"field": "new_status"},
            )

        # Phase 2: Per-activity processing
        succeeded: list[Task] = []
        failed: list[BulkUpdateFailedItem] = []

        for activity_id in activity_ids:
            # Get existing activity
            existing = await self.repository.get_by_id(activity_id)

            if not existing:
                # Activity not found
                failed.append(
                    BulkUpdateFailedItem(
                        activity_id=activity_id,
                        error_code=ErrorCode.NOT_FOUND,
                        message=f"Activity with ID {activity_id} does not exist",
                    )
                )
                continue

            # Check if transition is valid
            if not self._is_valid_transition(existing.status, validated_status):
                failed.append(
                    BulkUpdateFailedItem(
                        activity_id=activity_id,
                        error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                        message=f"Cannot transition from {existing.status} to {validated_status}",
                    )
                )
                continue

            # Update activity
            task_update = TaskUpdate.model_validate({"status": validated_status})
            updated_task = await self.repository.update(
                activity_id,
                task_update,
            )

            if not updated_task:
                # Shouldn't happen, but handle gracefully
                failed.append(
                    BulkUpdateFailedItem(
                        activity_id=activity_id,
                        error_code=ErrorCode.NOT_FOUND,
                        message=f"Activity with ID {activity_id} not found",
                    )
                )
                continue

            # Create activity log entry
            await self._create_activity_log(
                activity_id=activity_id,
                action="status_changed",
                old_status=existing.status,
                new_status=validated_status,
                current_user_id=current_user_id,
            )

            # Publish event
            await self.event_bus.publish(
                "TASK_STATUS_CHANGED",
                {
                    "activity_id": activity_id,
                    "old_status": existing.status,
                    "new_status": validated_status,
                    "updated_at": updated_task.updated_at.isoformat(),
                    "updated_by": current_user_id,
                    "bulk_update": True,
                    "context": "shift_handover",
                },
            )

            succeeded.append(updated_task)

        # Phase 3: Response
        total = len(activity_ids)
        summary = BulkUpdateSummary(
            total=total,
            succeeded=len(succeeded),
            failed=len(failed),
        )

        return BulkActivityStatusUpdateResult(
            succeeded=succeeded,
            failed=failed,
            summary=summary,
        )

    async def _create_activity_log(
        self,
        activity_id: str,
        action: str,
        old_status: str,
        new_status: str,
        current_user_id: str | None = None,
    ) -> None:
        """Create activity log entry.

        Args:
            activity_id: Activity ID
            action: Action performed
            old_status: Previous status
            new_status: New status
            current_user_id: User performing action
        """
        # Store in-memory activity logs (for testing)
        if not hasattr(self.repository, "_activity_logs"):
            self.repository._activity_logs = []  # type: ignore

        log_entry: dict[str, Any] = {
            "activity_id": activity_id,
            "action": action,
            "details": {
                "old_status": old_status,
                "new_status": new_status,
                "bulk_update": True,
                "context": "shift_handover",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            "created_by": current_user_id,
            "created_at": datetime.now(UTC).isoformat(),
        }

        self.repository._activity_logs.append(log_entry)  # type: ignore


async def get_activities_service() -> ActivitiesService:
    """Factory for activities service.

    Returns:
        ActivitiesService instance
    """
    repository = get_activities_repository()
    from src.shared.event_bus import get_event_bus

    event_bus = get_event_bus()

    return ActivitiesService(repository=repository, event_bus=event_bus)
