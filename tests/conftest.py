"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.activities.repository import get_activities_repository
from src.alerts.repository import get_alerts_repository
from src.main import app
from src.programmes.repository import get_programmes_repository
from src.reports.repository import get_reports_repository
from src.shared.event_bus import reset_event_bus
from src.staff.repository import get_staff_repository


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset all repositories and event bus before each test."""
    # Reset event bus
    reset_event_bus()

    # Reset all repositories to prevent test pollution
    get_activities_repository().reset()
    get_programmes_repository().reset()
    get_staff_repository().reset()
    get_alerts_repository().reset()
    get_reports_repository().reset()

    yield

    # Clean up after test
    reset_event_bus()
    get_activities_repository().reset()
    get_programmes_repository().reset()
    get_staff_repository().reset()
    get_alerts_repository().reset()
    get_reports_repository().reset()
