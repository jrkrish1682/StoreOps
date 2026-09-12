"""
Data models for Activities module.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    """Task status enumeration."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class TaskPriority(StrEnum):
    """Task priority enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskCategory(StrEnum):
    """Task category enumeration."""

    OPERATIONAL = "OPERATIONAL"
    COMPLIANCE = "COMPLIANCE"
    RESTOCKING = "RESTOCKING"
    PLANOGRAM = "PLANOGRAM"
    MAINTENANCE = "MAINTENANCE"


class TaskBase(BaseModel):
    """Base task model."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    category: TaskCategory = Field(...)
    assigned_user_id: str | None = None
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    """Request model for creating task."""


class TaskUpdate(BaseModel):
    """Request model for updating task."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    category: TaskCategory | None = None
    assigned_user_id: str | None = None
    due_date: datetime | None = None


class Task(TaskBase):
    """Response model for task."""

    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None

    model_config = {"from_attributes": True}


class TaskList(BaseModel):
    """Response model for task list."""

    items: list[Task]
    total: int
    skip: int
    limit: int


# Activity log models
class ActivityLogBase(BaseModel):
    """Base activity log model."""

    task_id: str
    action: str = Field(..., min_length=1, max_length=100)
    details: dict | None = None


class ActivityLog(ActivityLogBase):
    """Response model for activity log."""

    id: str
    created_at: datetime
    created_by: str | None = None

    model_config = {"from_attributes": True}


# Bulk update models
class BulkActivityStatusUpdate(BaseModel):
    """Request model for bulk status update."""

    activity_ids: list[str] = Field(...)
    new_status: str = Field(...)  # Accept string to validate in service


class BulkUpdateFailedItem(BaseModel):
    """Failed item in bulk update response."""

    activity_id: str
    error_code: str
    message: str


class BulkUpdateSummary(BaseModel):
    """Summary of bulk update operation."""

    total: int
    succeeded: int
    failed: int


class BulkActivityStatusUpdateResult(BaseModel):
    """Response model for bulk status update."""

    succeeded: list[Task]
    failed: list[BulkUpdateFailedItem]
    summary: BulkUpdateSummary

    model_config = {"from_attributes": True}
