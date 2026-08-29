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

from src.activities.models import Task, TaskCreate, TaskStatus, TaskUpdate
from src.activities.repository import ActivitiesRepository, get_activities_repository
from src.shared.errors import NotFoundError, ValidationError
from src.shared.event_bus import EventBus, EventType


class ActivitiesService:
    """Service for managing activities/tasks."""

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
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
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


async def get_activities_service() -> ActivitiesService:
    """Factory for activities service.

    Returns:
        ActivitiesService instance
    """
    repository = get_activities_repository()
    from src.shared.event_bus import get_event_bus

    event_bus = get_event_bus()

    return ActivitiesService(repository=repository, event_bus=event_bus)
