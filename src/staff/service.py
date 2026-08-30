"""Service layer for Staff module."""

from src.shared.errors import ConflictError, NotFoundError, ValidationError
from src.shared.event_bus import EventBus, EventType
from src.staff.models import Staff, StaffCreate, StaffUpdate
from src.staff.repository import StaffRepository, get_staff_repository


class StaffService:
    """Service for managing staff."""

    def __init__(
        self,
        repository: StaffRepository,
        event_bus: EventBus,
    ) -> None:
        """Initialize service."""
        self.repository = repository
        self.event_bus = event_bus

    async def create_staff(self, staff_create: StaffCreate) -> Staff:
        """Create new staff member."""
        if not staff_create.first_name or not staff_create.first_name.strip():
            raise ValidationError(message="First name is required")

        existing = await self.repository.get_by_email(staff_create.email)
        if existing:
            raise ConflictError(
                resource_type="Staff",
                message=f"Staff member with email {staff_create.email} already exists",
            )

        staff = await self.repository.create(staff_create)

        await self.event_bus.publish(
            EventType.STAFF_ONBOARDED,
            {
                "staff_id": staff.id,
                "name": f"{staff.first_name} {staff.last_name}",
                "role": staff.role,
            },
        )

        return staff

    async def get_staff(self, staff_id: str) -> Staff:
        """Get staff member by ID."""
        staff = await self.repository.get_by_id(staff_id)
        if not staff:
            raise NotFoundError(resource_type="Staff", resource_id=staff_id)
        return staff

    async def list_staff(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List staff members."""
        staff, total = await self.repository.list_all(skip=skip, limit=limit)
        return {
            "items": staff,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def list_store_staff(
        self,
        store_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> dict:
        """List staff by store."""
        staff, total = await self.repository.list_by_store(
            store_id=store_id,
            skip=skip,
            limit=limit,
        )
        return {
            "items": staff,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_staff(self, staff_id: str, staff_update: StaffUpdate) -> Staff:
        """Update staff member."""
        existing = await self.repository.get_by_id(staff_id)
        if not existing:
            raise NotFoundError(resource_type="Staff", resource_id=staff_id)

        updated = await self.repository.update(staff_id, staff_update)
        if not updated:
            raise NotFoundError(resource_type="Staff", resource_id=staff_id)

        return updated

    async def delete_staff(self, staff_id: str) -> bool:
        """Delete staff member."""
        deleted = await self.repository.delete(staff_id)
        if not deleted:
            raise NotFoundError(resource_type="Staff", resource_id=staff_id)

        await self.event_bus.publish(
            EventType.STAFF_OFFBOARDED,
            {"staff_id": staff_id},
        )

        return True


async def get_staff_service() -> StaffService:
    """Factory for staff service."""
    repository = get_staff_repository()
    from src.shared.event_bus import get_event_bus

    event_bus = get_event_bus()

    return StaffService(repository=repository, event_bus=event_bus)
