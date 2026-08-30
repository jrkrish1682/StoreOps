"""Service layer for Programmes module."""

from src.programmes.models import Programme, ProgrammeCreate, ProgrammeUpdate
from src.programmes.repository import ProgrammesRepository, get_programmes_repository
from src.shared.errors import NotFoundError, ValidationError
from src.shared.event_bus import EventBus, EventType


class ProgrammesService:
    """Service for managing programmes."""

    def __init__(
        self,
        repository: ProgrammesRepository,
        event_bus: EventBus,
    ) -> None:
        """Initialize service."""
        self.repository = repository
        self.event_bus = event_bus

    async def create_programme(
        self,
        programme_create: ProgrammeCreate,
        current_user_id: str | None = None,
    ) -> Programme:
        """Create new programme."""
        if not programme_create.name or not programme_create.name.strip():
            raise ValidationError(message="Programme name is required")

        programme = await self.repository.create(
            programme_create=programme_create,
            created_by=current_user_id,
        )

        await self.event_bus.publish(
            EventType.PROGRAMME_CREATED,
            {
                "programme_id": programme.id,
                "name": programme.name,
                "type": programme.programme_type,
            },
        )

        return programme

    async def get_programme(self, programme_id: str) -> Programme:
        """Get programme by ID."""
        programme = await self.repository.get_by_id(programme_id)
        if not programme:
            raise NotFoundError(resource_type="Programme", resource_id=programme_id)
        return programme

    async def list_programmes(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List programmes with pagination."""
        programmes, total = await self.repository.list_all(skip=skip, limit=limit)
        return {
            "items": programmes,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_programme(
        self,
        programme_id: str,
        programme_update: ProgrammeUpdate,
    ) -> Programme:
        """Update programme."""
        existing = await self.repository.get_by_id(programme_id)
        if not existing:
            raise NotFoundError(resource_type="Programme", resource_id=programme_id)

        if programme_update.name is not None:
            if not programme_update.name or not programme_update.name.strip():
                raise ValidationError(message="Programme name cannot be empty")

        updated_programme = await self.repository.update(programme_id, programme_update)
        if not updated_programme:
            raise NotFoundError(resource_type="Programme", resource_id=programme_id)

        return updated_programme

    async def delete_programme(self, programme_id: str) -> bool:
        """Delete programme."""
        deleted = await self.repository.delete(programme_id)
        if not deleted:
            raise NotFoundError(resource_type="Programme", resource_id=programme_id)
        return True


async def get_programmes_service() -> ProgrammesService:
    """Factory for programmes service."""
    repository = get_programmes_repository()
    from src.shared.event_bus import get_event_bus

    event_bus = get_event_bus()

    return ProgrammesService(repository=repository, event_bus=event_bus)
