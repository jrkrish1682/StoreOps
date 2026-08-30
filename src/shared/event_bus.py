"""
In-memory event bus for cross-module communication.

Modules communicate side effects via events only.
Example:
    Activities module publishes TASK_COMPLETED event.
    Alerts module subscribes to TASK_COMPLETED and triggers escalations.
    Alerts module NEVER calls ActivitiesService.
"""

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

# Event handler type: async function that receives event payload
EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventType(StrEnum):
    """Standard event types published across modules."""

    # Activities events
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_OVERDUE = "TASK_OVERDUE"
    TASK_ASSIGNED = "TASK_ASSIGNED"

    # Programmes events
    PROGRAMME_CREATED = "PROGRAMME_CREATED"
    PROGRAMME_STARTED = "PROGRAMME_STARTED"
    PROGRAMME_COMPLETED = "PROGRAMME_COMPLETED"

    # Staff events
    STAFF_ONBOARDED = "STAFF_ONBOARDED"
    STAFF_OFFBOARDED = "STAFF_OFFBOARDED"

    # Alerts events
    SLA_BREACH = "SLA_BREACH"
    CRITICAL_ALERT = "CRITICAL_ALERT"
    ESCALATION_NEEDED = "ESCALATION_NEEDED"

    # Reports events
    REPORT_GENERATED = "REPORT_GENERATED"


class EventBus:
    """Lightweight in-memory event bus."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[str, list[EventHandler]] = {}
        self._event_history: list[tuple[str, dict[str, Any]]] = []

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to call when event is published

        Returns:
            Unsubscribe function
        """
        event_key = str(event_type)
        if event_key not in self._handlers:
            self._handlers[event_key] = []

        self._handlers[event_key].append(handler)

        def unsubscribe() -> None:
            self._handlers[event_key].remove(handler)

        return unsubscribe

    async def publish(
        self,
        event_type: EventType | str,
        payload: dict[str, Any],
    ) -> None:
        """Publish event to all subscribers.

        Args:
            event_type: Type of event
            payload: Event data
        """
        event_key = str(event_type)
        self._event_history.append((event_key, payload))

        if event_key not in self._handlers:
            return

        for handler in self._handlers[event_key]:
            await handler(payload)

    def get_event_history(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all published events (for testing/debugging)."""
        return self._event_history.copy()

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    def reset(self) -> None:
        """Reset event bus (clear handlers and history)."""
        self._handlers.clear()
        self._event_history.clear()


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset event bus (useful for testing)."""
    global _event_bus
    _event_bus = EventBus()
