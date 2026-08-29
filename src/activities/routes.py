"""
Route handlers for Activities module.

Responsibilities:
- HTTP request/response handling
- No business logic
- Call services only
- Format responses
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.activities.models import Task, TaskCreate, TaskList, TaskUpdate
from src.activities.service import ActivitiesService, get_activities_service
from src.shared.errors import AppError

router = APIRouter(
    prefix="/api/v1/activities",
    tags=["activities"],
)


@router.post(
    "/tasks",
    response_model=Task,
    status_code=201,
)
async def create_task(
    task_create: TaskCreate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Create new task.

    Args:
        task_create: Task creation data
        service: Activities service

    Returns:
        Created task

    Raises:
        HTTPException: If validation fails
    """
    try:
        return await service.create_task(task_create=task_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
)
async def get_task(
    task_id: str,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Get task by ID.

    Args:
        task_id: Task ID
        service: Activities service

    Returns:
        Task

    Raises:
        HTTPException: If task not found
    """
    try:
        return await service.get_task(task_id=task_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/tasks",
    response_model=TaskList,
)
async def list_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ActivitiesService = Depends(get_activities_service),
) -> TaskList:
    """List tasks with pagination.

    Args:
        skip: Number of items to skip
        limit: Maximum items to return
        service: Activities service

    Returns:
        Paginated task list
    """
    result = await service.list_tasks(skip=skip, limit=limit)
    return TaskList(**result)


@router.put(
    "/tasks/{task_id}",
    response_model=Task,
)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    service: ActivitiesService = Depends(get_activities_service),
) -> Task:
    """Update task.

    Args:
        task_id: Task ID
        task_update: Update data
        service: Activities service

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found or validation fails
    """
    try:
        return await service.update_task(task_id=task_id, task_update=task_update)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.delete(
    "/tasks/{task_id}",
    status_code=204,
)
async def delete_task(
    task_id: str,
    service: ActivitiesService = Depends(get_activities_service),
) -> None:
    """Delete task.

    Args:
        task_id: Task ID
        service: Activities service

    Raises:
        HTTPException: If task not found
    """
    try:
        await service.delete_task(task_id=task_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/tasks/status/{status}",
    response_model=TaskList,
)
async def get_tasks_by_status(
    status: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ActivitiesService = Depends(get_activities_service),
) -> TaskList:
    """Get tasks filtered by status.

    Args:
        status: Task status
        skip: Number of items to skip
        limit: Maximum items to return
        service: Activities service

    Returns:
        Paginated task list
    """
    result = await service.get_tasks_by_status(
        status=status,
        skip=skip,
        limit=limit,
    )
    return TaskList(**result)


@router.get(
    "/users/{user_id}/tasks",
    response_model=TaskList,
)
async def get_user_tasks(
    user_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ActivitiesService = Depends(get_activities_service),
) -> TaskList:
    """Get tasks assigned to user.

    Args:
        user_id: User ID
        skip: Number of items to skip
        limit: Maximum items to return
        service: Activities service

    Returns:
        Paginated task list
    """
    result = await service.get_user_tasks(
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
    return TaskList(**result)
