"""Route handlers for Staff module."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.shared.errors import AppError
from src.staff.models import Staff, StaffCreate, StaffList, StaffUpdate
from src.staff.service import StaffService, get_staff_service

router = APIRouter(
    prefix="/api/v1/staff",
    tags=["staff"],
)


@router.post(
    "",
    response_model=Staff,
    status_code=201,
)
async def create_staff(
    staff_create: StaffCreate,
    service: StaffService = Depends(get_staff_service),
) -> Staff:
    """Create new staff member."""
    try:
        return await service.create_staff(staff_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/{staff_id}",
    response_model=Staff,
)
async def get_staff(
    staff_id: str,
    service: StaffService = Depends(get_staff_service),
) -> Staff:
    """Get staff member by ID."""
    try:
        return await service.get_staff(staff_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "",
    response_model=StaffList,
)
async def list_staff(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: StaffService = Depends(get_staff_service),
) -> StaffList:
    """List all staff members."""
    result = await service.list_staff(skip=skip, limit=limit)
    return StaffList(**result)


@router.get(
    "/stores/{store_id}",
    response_model=StaffList,
)
async def list_store_staff(
    store_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: StaffService = Depends(get_staff_service),
) -> StaffList:
    """List staff by store."""
    result = await service.list_store_staff(
        store_id=store_id,
        skip=skip,
        limit=limit,
    )
    return StaffList(**result)


@router.put(
    "/{staff_id}",
    response_model=Staff,
)
async def update_staff(
    staff_id: str,
    staff_update: StaffUpdate,
    service: StaffService = Depends(get_staff_service),
) -> Staff:
    """Update staff member."""
    try:
        return await service.update_staff(staff_id, staff_update)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.delete(
    "/{staff_id}",
    status_code=204,
)
async def delete_staff(
    staff_id: str,
    service: StaffService = Depends(get_staff_service),
) -> None:
    """Delete staff member."""
    try:
        await service.delete_staff(staff_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
