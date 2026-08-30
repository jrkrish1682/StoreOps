"""Repository layer for Programmes module."""

from datetime import UTC, datetime
from typing import Any

from src.programmes.models import Programme, ProgrammeCreate, ProgrammeUpdate


class ProgrammesRepository:
    """Repository for managing programmes."""

    def __init__(self) -> None:
        """Initialize repository with in-memory storage."""
        self._programmes: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(
        self,
        programme_create: ProgrammeCreate,
        created_by: str | None = None,
    ) -> Programme:
        """Create new programme."""
        self._counter += 1
        programme_id = f"prog_{self._counter}"
        now = datetime.now(UTC)

        programme_data = {
            "id": programme_id,
            "name": programme_create.name,
            "description": programme_create.description,
            "programme_type": programme_create.programme_type,
            "status": programme_create.status,
            "start_date": programme_create.start_date,
            "end_date": programme_create.end_date,
            "target_stores": programme_create.target_stores or [],
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
        }

        self._programmes[programme_id] = programme_data
        return Programme.model_validate(programme_data)

    async def get_by_id(self, programme_id: str) -> Programme | None:
        """Get programme by ID."""
        programme_data = self._programmes.get(programme_id)
        return Programme.model_validate(programme_data) if programme_data else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Programme], int]:
        """List all programmes with pagination."""
        all_programmes = list(self._programmes.values())
        total = len(all_programmes)
        programmes = all_programmes[skip : skip + limit]
        return [Programme.model_validate(p) for p in programmes], total
    async def update(
        self,
        programme_id: str,
        programme_update: ProgrammeUpdate,
    ) -> Programme | None:
        """Update programme."""
        programme_data = self._programmes.get(programme_id)
        if not programme_data:
            return None

        update_dict = programme_update.model_dump(exclude_unset=True)
        programme_data.update(update_dict)
        programme_data["updated_at"] = datetime.now(UTC)

        return Programme.model_validate(programme_data)

    async def delete(self, programme_id: str) -> bool:
        """Delete programme."""
        if programme_id in self._programmes:
            del self._programmes[programme_id]
            return True
        return False

    def reset(self) -> None:
        """Reset repository (for testing)."""
        self._programmes.clear()
        self._counter = 0


_repository: ProgrammesRepository | None = None


def get_programmes_repository() -> ProgrammesRepository:
    """Get global programmes repository instance."""
    global _repository
    if _repository is None:
        _repository = ProgrammesRepository()
    return _repository
