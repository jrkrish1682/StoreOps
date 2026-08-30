"""Route handlers for Reports module."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.reports.models import Report, ReportCreate, ReportList, ReportUpdate
from src.reports.service import ReportsService, get_reports_service
from src.shared.errors import AppError

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["reports"],
)


@router.post(
    "",
    response_model=Report,
    status_code=201,
)
async def create_report(
    report_create: ReportCreate,
    service: ReportsService = Depends(get_reports_service),
) -> Report:
    """Create new report."""
    try:
        return await service.create_report(report_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/{report_id}",
    response_model=Report,
)
async def get_report(
    report_id: str,
    service: ReportsService = Depends(get_reports_service),
) -> Report:
    """Get report by ID."""
    try:
        return await service.get_report(report_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "",
    response_model=ReportList,
)
async def list_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ReportsService = Depends(get_reports_service),
) -> ReportList:
    """List all reports."""
    result = await service.list_reports(skip=skip, limit=limit)
    return ReportList(**result)


@router.get(
    "/type/{report_type}",
    response_model=ReportList,
)
async def get_reports_by_type(
    report_type: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: ReportsService = Depends(get_reports_service),
) -> ReportList:
    """Get reports by type."""
    result = await service.list_by_type(
        report_type=report_type,
        skip=skip,
        limit=limit,
    )
    return ReportList(**result)


@router.put(
    "/{report_id}",
    response_model=Report,
)
async def update_report(
    report_id: str,
    report_update: ReportUpdate,
    service: ReportsService = Depends(get_reports_service),
) -> Report:
    """Update report."""
    try:
        return await service.update_report(report_id, report_update)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.delete(
    "/{report_id}",
    status_code=204,
)
async def delete_report(
    report_id: str,
    service: ReportsService = Depends(get_reports_service),
) -> None:
    """Delete report."""
    try:
        await service.delete_report(report_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
