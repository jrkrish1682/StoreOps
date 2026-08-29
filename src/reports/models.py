"""Data models for Reports module."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReportType(StrEnum):
    """Report type enumeration."""

    STORE_SUMMARY = "STORE_SUMMARY"
    REGIONAL_SUMMARY = "REGIONAL_SUMMARY"
    DEPARTMENT_PERFORMANCE = "DEPARTMENT_PERFORMANCE"
    ACTIVITY_METRICS = "ACTIVITY_METRICS"
    COMPLIANCE_REPORT = "COMPLIANCE_REPORT"


class ReportStatus(StrEnum):
    """Report status enumeration."""

    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"


class ReportBase(BaseModel):
    """Base report model."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    report_type: ReportType
    status: ReportStatus = Field(default=ReportStatus.DRAFT)
    period_start: datetime | None = None
    period_end: datetime | None = None
    scope_id: str | None = None  # store_id, region_id, or department_id
    scope_type: str | None = None  # STORE, REGION, DEPARTMENT


class ReportCreate(ReportBase):
    """Request model for creating report."""



class ReportUpdate(BaseModel):
    """Request model for updating report."""

    status: ReportStatus | None = None
    description: str | None = Field(None, max_length=2000)


class Report(ReportBase):
    """Response model for report."""

    id: str
    data: dict | None = None
    created_at: datetime
    updated_at: datetime
    generated_by: str | None = None

    model_config = {"from_attributes": True}


class ReportList(BaseModel):
    """Response model for report list."""

    items: list[Report]
    total: int
    skip: int
    limit: int
