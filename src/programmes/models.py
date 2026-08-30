"""Data models for Programmes module."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProgrammeStatus(StrEnum):
    """Programme status enumeration."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProgrammeType(StrEnum):
    """Programme type enumeration."""

    INITIATIVE = "INITIATIVE"
    CAMPAIGN = "CAMPAIGN"
    ROLLOUT = "ROLLOUT"
    PROMOTION = "PROMOTION"


class ProgrammeBase(BaseModel):
    """Base programme model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    programme_type: ProgrammeType
    status: ProgrammeStatus = Field(default=ProgrammeStatus.DRAFT)
    start_date: datetime | None = None
    end_date: datetime | None = None
    target_stores: list[str] | None = None


class ProgrammeCreate(ProgrammeBase):
    """Request model for creating programme."""



class ProgrammeUpdate(BaseModel):
    """Request model for updating programme."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    status: ProgrammeStatus | None = None
    end_date: datetime | None = None
    target_stores: list[str] | None = None


class Programme(ProgrammeBase):
    """Response model for programme."""

    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None

    model_config = {"from_attributes": True}


class ProgrammeList(BaseModel):
    """Response model for programme list."""

    items: list[Programme]
    total: int
    skip: int
    limit: int
