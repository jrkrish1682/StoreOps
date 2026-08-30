"""Tests for Event Bus."""

import pytest

from src.shared.event_bus import EventBus, EventType, reset_event_bus


@pytest.fixture
def event_bus() -> EventBus:
    """Create event bus instance."""
    reset_event_bus()
    from src.shared.event_bus import get_event_bus
    return get_event_bus()


class TestEventBus:
    """Tests for event bus."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus: EventBus) -> None:
        """Test publishing and subscribing to events."""
        received_events = []

        async def handler(payload: dict) -> None:
            received_events.append(payload)

        # Subscribe to event
        event_bus.subscribe(EventType.TASK_CREATED, handler)

        # Publish event
        await event_bus.publish(
            EventType.TASK_CREATED,
            {"task_id": "123", "title": "Test Task"},
        )

        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]["task_id"] == "123"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus: EventBus) -> None:
        """Test multiple subscribers to same event."""
        calls = []

        async def handler1(payload: dict) -> None:
            calls.append(("handler1", payload))

        async def handler2(payload: dict) -> None:
            calls.append(("handler2", payload))

        # Subscribe both handlers
        event_bus.subscribe(EventType.PROGRAMME_CREATED, handler1)
        event_bus.subscribe(EventType.PROGRAMME_CREATED, handler2)

        # Publish event
        await event_bus.publish(
            EventType.PROGRAMME_CREATED,
            {"programme_id": "456"},
        )

        # Verify both handlers received event
        assert len(calls) == 2
        assert calls[0][0] == "handler1"
        assert calls[1][0] == "handler2"

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus: EventBus) -> None:
        """Test unsubscribing from events."""
        received = []

        async def handler(payload: dict) -> None:
            received.append(payload)

        # Subscribe, then unsubscribe
        unsubscribe = event_bus.subscribe(EventType.TASK_COMPLETED, handler)
        unsubscribe()

        # Publish event
        await event_bus.publish(
            EventType.TASK_COMPLETED,
            {"task_id": "789"},
        )

        # Verify handler was not called
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_event_history(self, event_bus: EventBus) -> None:
        """Test event history tracking."""
        # Publish multiple events
        await event_bus.publish(EventType.TASK_CREATED, {"task_id": "1"})
        await event_bus.publish(EventType.PROGRAMME_CREATED, {"programme_id": "2"})
        await event_bus.publish(EventType.TASK_COMPLETED, {"task_id": "1"})

        # Verify history
        history = event_bus.get_event_history()
        assert len(history) == 3
        assert history[0][0] == EventType.TASK_CREATED
        assert history[1][0] == EventType.PROGRAMME_CREATED
        assert history[2][0] == EventType.TASK_COMPLETED

    def test_clear_history(self, event_bus: EventBus) -> None:
        """Test clearing event history."""
        import asyncio
        asyncio.run(event_bus.publish(EventType.TASK_CREATED, {"task_id": "1"}))

        history = event_bus.get_event_history()
        assert len(history) == 1

        event_bus.clear_history()
        history = event_bus.get_event_history()
        assert len(history) == 0
