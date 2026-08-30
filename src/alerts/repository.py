"""Repository layer for Alerts module."""

from datetime import UTC, datetime
from typing import Any

from src.alerts.models import Alert, AlertCreate, AlertUpdate


class AlertsRepository:
    """Repository for managing alerts."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._alerts: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, alert_create: AlertCreate) -> Alert:
        """Create new alert."""
        self._counter += 1
        alert_id = f"alert_{self._counter}"
        now = datetime.now(UTC)

        alert_data = {
            "id": alert_id,
            "title": alert_create.title,
            "description": alert_create.description,
            "alert_type": alert_create.alert_type,
            "severity": alert_create.severity,
            "status": alert_create.status,
            "related_entity_id": alert_create.related_entity_id,
            "related_entity_type": alert_create.related_entity_type,
            "store_id": alert_create.store_id,
            "created_at": now,
            "updated_at": now,
        }

        self._alerts[alert_id] = alert_data
        return Alert.model_validate(alert_data)

    async def get_by_id(self, alert_id: str) -> Alert | None:
        """Get alert by ID."""
        alert_data = self._alerts.get(alert_id)
        return Alert.model_validate(alert_data) if alert_data else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Alert], int]:
        """List all alerts."""
        all_alerts = list(self._alerts.values())
        total = len(all_alerts)
        alerts = all_alerts[skip : skip + limit]
        return [Alert.model_validate(a) for a in alerts], total
    async def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Alert], int]:
        """List alerts by status."""
        filtered = [a for a in self._alerts.values() if a["status"] == status]
        total = len(filtered)
        alerts = filtered[skip : skip + limit]
        return [Alert.model_validate(a) for a in alerts], total
    async def list_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Alert], int]:
        """List alerts by severity."""
        filtered = [a for a in self._alerts.values() if a["severity"] == severity]
        total = len(filtered)
        alerts = filtered[skip : skip + limit]
        return [Alert.model_validate(a) for a in alerts], total
    async def update(self, alert_id: str, alert_update: AlertUpdate) -> Alert | None:
        """Update alert."""
        alert_data = self._alerts.get(alert_id)
        if not alert_data:
            return None

        update_dict = alert_update.model_dump(exclude_unset=True)
        alert_data.update(update_dict)
        alert_data["updated_at"] = datetime.now(UTC)

        return Alert.model_validate(alert_data)

    async def delete(self, alert_id: str) -> bool:
        """Delete alert."""
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            return True
        return False

    def reset(self) -> None:
        """Reset repository."""
        self._alerts.clear()
        self._counter = 0


_repository: AlertsRepository | None = None


def get_alerts_repository() -> AlertsRepository:
    """Get global alerts repository instance."""
    global _repository
    if _repository is None:
        _repository = AlertsRepository()
    return _repository
