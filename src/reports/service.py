"""Service layer for Reports module."""

from src.reports.models import Report, ReportCreate, ReportUpdate
from src.reports.repository import ReportsRepository, get_reports_repository
from src.shared.errors import NotFoundError, ValidationError
from src.shared.event_bus import EventBus, EventType


class ReportsService:
    """Service for managing reports."""

    def __init__(
        self,
        repository: ReportsRepository,
        event_bus: EventBus,
    ) -> None:
        """Initialize service."""
        self.repository = repository
        self.event_bus = event_bus

    async def create_report(self, report_create: ReportCreate) -> Report:
        """Create new report."""
        if not report_create.title or not report_create.title.strip():
            raise ValidationError(message="Report title is required")

        report = await self.repository.create(report_create)
        return report

    async def get_report(self, report_id: str) -> Report:
        """Get report by ID."""
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(resource_type="Report", resource_id=report_id)
        return report

    async def list_reports(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List all reports."""
        reports, total = await self.repository.list_all(skip=skip, limit=limit)
        return {
            "items": reports,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def list_by_type(
        self,
        report_type: str,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List reports by type."""
        reports, total = await self.repository.list_by_type(
            report_type=report_type,
            skip=skip,
            limit=limit,
        )
        return {
            "items": reports,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_report(self, report_id: str, report_update: ReportUpdate) -> Report:
        """Update report."""
        existing = await self.repository.get_by_id(report_id)
        if not existing:
            raise NotFoundError(resource_type="Report", resource_id=report_id)

        updated = await self.repository.update(report_id, report_update)
        if not updated:
            raise NotFoundError(resource_type="Report", resource_id=report_id)

        await self.event_bus.publish(
            EventType.REPORT_GENERATED,
            {
                "report_id": updated.id,
                "title": updated.title,
                "type": updated.report_type,
            },
        )

        return updated

    async def delete_report(self, report_id: str) -> bool:
        """Delete report."""
        deleted = await self.repository.delete(report_id)
        if not deleted:
            raise NotFoundError(resource_type="Report", resource_id=report_id)
        return True


async def get_reports_service() -> ReportsService:
    """Factory for reports service."""
    repository = get_reports_repository()
    from src.shared.event_bus import get_event_bus

    event_bus = get_event_bus()

    return ReportsService(repository=repository, event_bus=event_bus)
