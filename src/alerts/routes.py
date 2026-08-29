"""Route handlers for Alerts module."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.alerts.models import Alert, AlertCreate, AlertList, AlertUpdate
from src.alerts.service import AlertsService, get_alerts_service
from src.shared.errors import AppError

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["alerts"],
)


@router.post(
    "",
    response_model=Alert,
    status_code=201,
)
async def create_alert(
    alert_create: AlertCreate,
    service: AlertsService = Depends(get_alerts_service),
) -> Alert:
    """Create new alert."""
    try:
        return await service.create_alert(alert_create)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "/{alert_id}",
    response_model=Alert,
)
async def get_alert(
    alert_id: str,
    service: AlertsService = Depends(get_alerts_service),
) -> Alert:
    """Get alert by ID."""
    try:
        return await service.get_alert(alert_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.get(
    "",
    response_model=AlertList,
)
async def list_alerts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: AlertsService = Depends(get_alerts_service),
) -> AlertList:
    """List all alerts."""
    result = await service.list_alerts(skip=skip, limit=limit)
    return AlertList(**result)


@router.get(
    "/status/{status}",
    response_model=AlertList,
)
async def get_alerts_by_status(
    status: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: AlertsService = Depends(get_alerts_service),
) -> AlertList:
    """Get alerts by status."""
    result = await service.list_by_status(
        status=status,
        skip=skip,
        limit=limit,
    )
    return AlertList(**result)


@router.get(
    "/severity/{severity}",
    response_model=AlertList,
)
async def get_alerts_by_severity(
    severity: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    service: AlertsService = Depends(get_alerts_service),
) -> AlertList:
    """Get alerts by severity."""
    result = await service.list_by_severity(
        severity=severity,
        skip=skip,
        limit=limit,
    )
    return AlertList(**result)


@router.put(
    "/{alert_id}",
    response_model=Alert,
)
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    service: AlertsService = Depends(get_alerts_service),
) -> Alert:
    """Update alert."""
    try:
        return await service.update_alert(alert_id, alert_update)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())


@router.delete(
    "/{alert_id}",
    status_code=204,
)
async def delete_alert(
    alert_id: str,
    service: AlertsService = Depends(get_alerts_service),
) -> None:
    """Delete alert."""
    try:
        await service.delete_alert(alert_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
