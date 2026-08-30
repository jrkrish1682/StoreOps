"""Repository layer for Reports module."""

from datetime import UTC, datetime
from typing import Any

from src.reports.models import Report, ReportCreate, ReportUpdate


class ReportsRepository:
    """Repository for managing reports."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._reports: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, report_create: ReportCreate) -> Report:
        """Create new report."""
        self._counter += 1
        report_id = f"report_{self._counter}"
        now = datetime.now(UTC)

        report_data = {
            "id": report_id,
            "title": report_create.title,
            "description": report_create.description,
            "report_type": report_create.report_type,
            "status": report_create.status,
            "period_start": report_create.period_start,
            "period_end": report_create.period_end,
            "scope_id": report_create.scope_id,
            "scope_type": report_create.scope_type,
            "data": None,
            "created_at": now,
            "updated_at": now,
            "generated_by": None,
        }

        self._reports[report_id] = report_data
        return Report.model_validate(report_data)

    async def get_by_id(self, report_id: str) -> Report | None:
        """Get report by ID."""
        report_data = self._reports.get(report_id)
        return Report.model_validate(report_data) if report_data else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Report], int]:
        """List all reports."""
        all_reports = list(self._reports.values())
        total = len(all_reports)
        reports = all_reports[skip : skip + limit]
        return [Report.model_validate(r) for r in reports], total
    async def list_by_type(
        self,
        report_type: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Report], int]:
        """List reports by type."""
        filtered = [r for r in self._reports.values() if r["report_type"] == report_type]
        total = len(filtered)
        reports = filtered[skip : skip + limit]
        return [Report.model_validate(r) for r in reports], total
    async def update(self, report_id: str, report_update: ReportUpdate) -> Report | None:
        """Update report."""
        report_data = self._reports.get(report_id)
        if not report_data:
            return None

        update_dict = report_update.model_dump(exclude_unset=True)
        report_data.update(update_dict)
        report_data["updated_at"] = datetime.now(UTC)

        return Report.model_validate(report_data)

    async def delete(self, report_id: str) -> bool:
        """Delete report."""
        if report_id in self._reports:
            del self._reports[report_id]
            return True
        return False

    def reset(self) -> None:
        """Reset repository."""
        self._reports.clear()
        self._counter = 0


_repository: ReportsRepository | None = None


def get_reports_repository() -> ReportsRepository:
    """Get global reports repository instance."""
    global _repository
    if _repository is None:
        _repository = ReportsRepository()
    return _repository
