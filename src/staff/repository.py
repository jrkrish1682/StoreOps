"""Repository layer for Staff module."""

from datetime import UTC, datetime
from typing import Any

from src.staff.models import Staff, StaffCreate, StaffUpdate


class StaffRepository:
    """Repository for managing staff."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._staff: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def create(self, staff_create: StaffCreate) -> Staff:
        """Create new staff member."""
        self._counter += 1
        staff_id = f"staff_{self._counter}"
        now = datetime.now(UTC)

        staff_data = {
            "id": staff_id,
            "first_name": staff_create.first_name,
            "last_name": staff_create.last_name,
            "email": staff_create.email,
            "phone_number": staff_create.phone_number,
            "role": staff_create.role,
            "status": staff_create.status,
            "store_id": staff_create.store_id,
            "manager_id": staff_create.manager_id,
            "created_at": now,
            "updated_at": now,
        }

        self._staff[staff_id] = staff_data
        return Staff.model_validate(staff_data)

    async def get_by_id(self, staff_id: str) -> Staff | None:
        """Get staff member by ID."""
        staff_data = self._staff.get(staff_id)
        return Staff.model_validate(staff_data) if staff_data else None

    async def get_by_email(self, email: str) -> Staff | None:
        """Get staff member by email."""
        for staff_data in self._staff.values():
            if staff_data["email"] == email:
                return Staff.model_validate(staff_data)
        return None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Staff], int]:
        """List all staff members."""
        all_staff = list(self._staff.values())
        total = len(all_staff)
        staff = all_staff[skip : skip + limit]
        return [Staff.model_validate(s) for s in staff], total
    async def list_by_store(
        self,
        store_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Staff], int]:
        """List staff by store."""
        filtered = [s for s in self._staff.values() if s["store_id"] == store_id]
        total = len(filtered)
        staff = filtered[skip : skip + limit]
        return [Staff.model_validate(s) for s in staff], total
    async def update(self, staff_id: str, staff_update: StaffUpdate) -> Staff | None:
        """Update staff member."""
        staff_data = self._staff.get(staff_id)
        if not staff_data:
            return None

        update_dict = staff_update.model_dump(exclude_unset=True)
        staff_data.update(update_dict)
        staff_data["updated_at"] = datetime.now(UTC)

        return Staff.model_validate(staff_data)

    async def delete(self, staff_id: str) -> bool:
        """Delete staff member."""
        if staff_id in self._staff:
            del self._staff[staff_id]
            return True
        return False

    def reset(self) -> None:
        """Reset repository."""
        self._staff.clear()
        self._counter = 0


_repository: StaffRepository | None = None


def get_staff_repository() -> StaffRepository:
    """Get global staff repository instance."""
    global _repository
    if _repository is None:
        _repository = StaffRepository()
    return _repository
