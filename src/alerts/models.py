"""Data models for Alerts module."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AlertSeverity(StrEnum):
    """Alert severity enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(StrEnum):
    """Alert status enumeration."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertType(StrEnum):
    """Alert type enumeration."""

    SLA_BREACH = "SLA_BREACH"
    TASK_OVERDUE = "TASK_OVERDUE"
    LOW_INVENTORY = "LOW_INVENTORY"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    STAFFING_ISSUE = "STAFFING_ISSUE"


class AlertBase(BaseModel):
    """Base alert model."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.OPEN)
    related_entity_id: str | None = None
    related_entity_type: str | None = None
    store_id: str | None = None


class AlertCreate(AlertBase):
    """Request model for creating alert."""



class AlertUpdate(BaseModel):
    """Request model for updating alert."""

    status: AlertStatus | None = None
    description: str | None = Field(None, max_length=2000)


class Alert(AlertBase):
    """Response model for alert."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertList(BaseModel):
    """Response model for alert list."""

    items: list[Alert]
    total: int
    skip: int
    limit: int
