"""
Repository layer for Activities module.

Responsibilities:
- Direct data access
- No business logic
- No external service calls
- No service imports (circular dependency prevention)
"""

from datetime import UTC, datetime
from typing import Any

from src.activities.models import Task, TaskCreate, TaskUpdate


class ActivitiesRepository:
    """Repository for managing tasks."""

    def __init__(self) -> None:
        """Initialize repository with in-memory storage."""
        self._tasks: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, task_create: TaskCreate, created_by: str | None = None) -> Task:
        """Create new task.

        Args:
            task_create: Task creation data
            created_by: User ID who created task

        Returns:
            Created task
        """
        self._counter += 1
        task_id = f"task_{self._counter}"
        now = datetime.now(UTC)

        task_data = {
            "id": task_id,
            "title": task_create.title,
            "description": task_create.description,
            "status": task_create.status,
            "priority": task_create.priority,
            "category": task_create.category,
            "assigned_user_id": task_create.assigned_user_id,
            "due_date": task_create.due_date,
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
        }

        self._tasks[task_id] = task_data
        return Task.model_validate(task_data)

    async def get_by_id(self, task_id: str) -> Task | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        task_data = self._tasks.get(task_id)
        return Task.model_validate(task_data) if task_data else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Task], int]:
        """List all tasks with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Tuple of (tasks, total_count)
        """
        all_tasks = list(self._tasks.values())
        total = len(all_tasks)
        tasks = all_tasks[skip : skip + limit]
        return [Task.model_validate(t) for t in tasks], total
    async def update(self, task_id: str, task_update: TaskUpdate) -> Task | None:
        """Update task.

        Args:
            task_id: Task ID
            task_update: Update data

        Returns:
            Updated task or None if not found
        """
        task_data = self._tasks.get(task_id)
        if not task_data:
            return None

        # Update fields that are provided
        update_dict = task_update.model_dump(exclude_unset=True)
        task_data.update(update_dict)
        task_data["updated_at"] = datetime.now(UTC)

        return Task.model_validate(task_data)

    async def delete(self, task_id: str) -> bool:
        """Delete task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    async def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Task], int]:
        """List tasks by status.

        Args:
            status: Task status
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Tuple of (tasks, total_count)
        """
        filtered_tasks = [t for t in self._tasks.values() if t["status"] == status]
        total = len(filtered_tasks)
        tasks = filtered_tasks[skip : skip + limit]
        return [Task.model_validate(t) for t in tasks], total
    async def list_by_assigned_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Task], int]:
        """List tasks assigned to user.

        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            Tuple of (tasks, total_count)
        """
        filtered_tasks = [
            t for t in self._tasks.values() if t["assigned_user_id"] == user_id
        ]
        total = len(filtered_tasks)
        tasks = filtered_tasks[skip : skip + limit]
        return [Task.model_validate(t) for t in tasks], total
    async def bulk_update_status(
        self,
        activity_ids: list[str],
        new_status: str,
    ) -> list[Task]:
        """Update status for multiple tasks.

        Args:
            activity_ids: List of task IDs
            new_status: New status value

        Returns:
            List of updated tasks (only successful ones)
        """
        updated_tasks: list[Task] = []
        for task_id in activity_ids:
            task_data = self._tasks.get(task_id)
            if task_data:
                task_data["status"] = new_status
                task_data["updated_at"] = datetime.now(UTC)
                updated_tasks.append(Task.model_validate(task_data))
        return updated_tasks

    def reset(self) -> None:
        """Reset repository (for testing)."""
        self._tasks.clear()
        self._counter = 0


# Global repository instance
_repository: ActivitiesRepository | None = None


def get_activities_repository() -> ActivitiesRepository:
    """Get global activities repository instance."""
    global _repository
    if _repository is None:
        _repository = ActivitiesRepository()
    return _repository
