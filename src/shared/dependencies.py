"""
Shared dependencies for FastAPI routes.
"""

from collections.abc import AsyncGenerator
from typing import Any

from src.shared.event_bus import EventBus, get_event_bus


async def get_event_bus_dependency() -> EventBus:
    """FastAPI dependency to inject event bus."""
    return get_event_bus()


class DatabaseSession:
    """Stub database session class for dependency injection."""

    async def __aenter__(self) -> "DatabaseSession":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Async context manager exit."""

    async def execute(self, query: str) -> Any:
        """Execute query (stub)."""
        return []

    async def commit(self) -> None:
        """Commit transaction (stub)."""

    async def rollback(self) -> None:
        """Rollback transaction (stub)."""


async def get_db_session() -> AsyncGenerator[DatabaseSession, None]:
    """FastAPI dependency to inject database session."""
    async with DatabaseSession() as session:
        yield session
