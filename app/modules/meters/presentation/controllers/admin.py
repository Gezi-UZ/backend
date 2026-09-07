from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.meters.domain.entities.schemas import MeterResponse, AdminMeterDetailResponse, MeterUpdate
from app.modules.meters.presentation.dependencies import get_list_all_meters_detailed_usecase, get_admin_update_meter_usecase
from app.modules.meters.application.usecases.list_all_meters_detailed import ListAllMetersDetailedUseCase
from app.modules.meters.application.usecases.admin_update_meter import AdminUpdateMeterUseCase
import uuid

router = APIRouter()

@router.get("/meters")
def list_all_meters(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: ListAllMetersDetailedUseCase = Depends(get_list_all_meters_detailed_usecase)
) -> Dict[str, Any]:
    """
    Admin endpoint to list all meters in the system with detailed information.
    """
    meters = usecase.execute(status=status, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "meters": [m.model_dump(by_alias=True) for m in meters]
        }
    }

@router.patch("/meters/{meter_id}")
def admin_update_meter(
    meter_id: uuid.UUID,
    update_data: MeterUpdate,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: AdminUpdateMeterUseCase = Depends(get_admin_update_meter_usecase)
) -> Dict[str, Any]:
    """
    Admin endpoint to update any meter's details.
    """
    meter = usecase.execute(meter_id, update_data)
    return {
        "success": True,
        "data": meter.model_dump(by_alias=True)
    }
