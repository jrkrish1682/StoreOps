"""Route handlers for Programmes module."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.programmes.models import Programme, ProgrammeCreate, ProgrammeList, ProgrammeUpdate
from src.programmes.service import ProgrammesService, get_programmes_service
from src.shared.errors import AppError

router = APIRouter(
    prefix="/api/v1/programmes",
    tags=["programmes"],
)


@router.post(
    "",
    response_model=Programme,
    status_code=201,
)
async def create_programme(
    programme_create: ProgrammeCreate,
    service: ProgrammesService = Depends(get_programmes_service),
) -> Programme:
    """Create new programme."""
    try:
        return await service.create_programme(programme_create=programme_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/{programme_id}",
    response_model=Programme,
)
async def get_programme(
    programme_id: str,
    service: ProgrammesService = Depends(get_programmes_service),
) -> Programme:
    """Get programme by ID."""
    try:
        return await service.get_programme(programme_id=programme_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "",
    response_model=ProgrammeList,
)
async def list_programmes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ProgrammesService = Depends(get_programmes_service),
) -> ProgrammeList:
    """List programmes with pagination."""
    result = await service.list_programmes(skip=skip, limit=limit)
    return ProgrammeList(**result)


@router.put(
    "/{programme_id}",
    response_model=Programme,
)
async def update_programme(
    programme_id: str,
    programme_update: ProgrammeUpdate,
    service: ProgrammesService = Depends(get_programmes_service),
) -> Programme:
    """Update programme."""
    try:
        return await service.update_programme(
            programme_id=programme_id,
            programme_update=programme_update,
        )
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.delete(
    "/{programme_id}",
    status_code=204,
)
async def delete_programme(
    programme_id: str,
    service: ProgrammesService = Depends(get_programmes_service),
) -> None:
    """Delete programme."""
    try:
        await service.delete_programme(programme_id=programme_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
