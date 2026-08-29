"""Data models for Staff module."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class StaffRole(StrEnum):
    """Staff role enumeration."""

    STORE_MANAGER = "STORE_MANAGER"
    DEPARTMENT_LEAD = "DEPARTMENT_LEAD"
    STAFF_MEMBER = "STAFF_MEMBER"
    REGIONAL_MANAGER = "REGIONAL_MANAGER"


class StaffStatus(StrEnum):
    """Staff employment status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"


class StaffBase(BaseModel):
    """Base staff model."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: str | None = None
    role: StaffRole
    status: StaffStatus = Field(default=StaffStatus.ACTIVE)
    store_id: str | None = None
    manager_id: str | None = None


class StaffCreate(StaffBase):
    """Request model for creating staff."""



class StaffUpdate(BaseModel):
    """Request model for updating staff."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone_number: str | None = None
    role: StaffRole | None = None
    status: StaffStatus | None = None
    manager_id: str | None = None


class Staff(StaffBase):
    """Response model for staff."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StaffList(BaseModel):
    """Response model for staff list."""

    items: list[Staff]
    total: int
    skip: int
    limit: int
