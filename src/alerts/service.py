"""Service layer for Alerts module."""

from src.alerts.models import Alert, AlertCreate, AlertUpdate
from src.alerts.repository import AlertsRepository, get_alerts_repository
from src.shared.errors import NotFoundError, ValidationError
from src.shared.event_bus import EventBus


class AlertsService:
    """Service for managing alerts."""

    def __init__(
        self,
        repository: AlertsRepository,
        event_bus: EventBus,
    ) -> None:
        """Initialize service."""
        self.repository = repository
        self.event_bus = event_bus

    async def create_alert(self, alert_create: AlertCreate) -> Alert:
        """Create new alert."""
        if not alert_create.title or not alert_create.title.strip():
            raise ValidationError(message="Alert title is required")

        alert = await self.repository.create(alert_create)
        return alert

    async def get_alert(self, alert_id: str) -> Alert:
        """Get alert by ID."""
        alert = await self.repository.get_by_id(alert_id)
        if not alert:
            raise NotFoundError(resource_type="Alert", resource_id=alert_id)
        return alert

    async def list_alerts(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List all alerts."""
        alerts, total = await self.repository.list_all(skip=skip, limit=limit)
        return {
            "items": alerts,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List alerts by status."""
        alerts, total = await self.repository.list_by_status(
            status=status,
            skip=skip,
            limit=limit,
        )
        return {
            "items": alerts,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def list_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List alerts by severity."""
        alerts, total = await self.repository.list_by_severity(
            severity=severity,
            skip=skip,
            limit=limit,
        )
        return {
            "items": alerts,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_alert(self, alert_id: str, alert_update: AlertUpdate) -> Alert:
        """Update alert."""
        existing = await self.repository.get_by_id(alert_id)
        if not existing:
            raise NotFoundError(resource_type="Alert", resource_id=alert_id)

        updated = await self.repository.update(alert_id, alert_update)
        if not updated:
            raise NotFoundError(resource_type="Alert", resource_id=alert_id)

        return updated

    async def delete_alert(self, alert_id: str) -> bool:
        """Delete alert."""
        deleted = await self.repository.delete(alert_id)
        if not deleted:
            raise NotFoundError(resource_type="Alert", resource_id=alert_id)
        return True


async def get_alerts_service() -> AlertsService:
    """Factory for alerts service."""
    repository = get_alerts_repository()
    from src.shared.event_bus import get_event_bus

    event_bus = get_event_bus()

    return AlertsService(repository=repository, event_bus=event_bus)
