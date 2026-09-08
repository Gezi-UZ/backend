from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.meters.domain.entities.schemas import MeterResponse, AdminMeterDetailResponse, MeterUpdate
from app.modules.meters.presentation.dependencies import (
    get_list_all_meters_detailed_usecase, 
    get_admin_update_meter_usecase,
    get_admin_create_meter_usecase,
    get_revoke_meter_access_usecase
)
from app.modules.meters.application.usecases.list_all_meters_detailed import ListAllMetersDetailedUseCase
from app.modules.meters.application.usecases.admin_update_meter import AdminUpdateMeterUseCase
from app.modules.meters.application.usecases.admin_create_meter import AdminCreateMeterUseCase
from app.modules.meters.domain.entities.schemas import AdminMeterCreate
from app.modules.recharges.presentation.dependencies import get_admin_generate_token_usecase
import uuid
from pydantic import BaseModel

class GenerateTokenRequest(BaseModel):
    amount: float

router = APIRouter()

@router.post("/meters", status_code=201)
def admin_create_meter(
    meter_data: AdminMeterCreate,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: AdminCreateMeterUseCase = Depends(get_admin_create_meter_usecase)
) -> Dict[str, Any]:
    """
    Admin endpoint to create a new meter and optionally allocate it.
    """
    meter = usecase.execute(meter_data)
    return {
        "success": True,
        "data": {
            "meter_id": str(meter.id),
            "status": meter.estado
        }
    }

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
    meter = usecase.execute(meter_id, update_data, admin_id=admin_user.id)
    return {
        "success": True,
        "data": meter.model_dump(by_alias=True)
    }

@router.post("/meters/{meter_id}/revoke-owner")
def admin_revoke_meter_owner(
    meter_id: uuid.UUID,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: Any = Depends(get_revoke_meter_access_usecase)
) -> Dict[str, Any]:
    """
    Admin endpoint to revoke the current owner of a meter.
    """
    meter = usecase.execute(meter_id, admin_id=admin_user.id)
    return {
        "success": True,
        "data": meter.model_dump(by_alias=True)
    }

@router.post("/meters/{meter_id}/generate-token")
def admin_generate_token(
    meter_id: uuid.UUID,
    data: GenerateTokenRequest,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: Any = Depends(get_admin_generate_token_usecase)
) -> Dict[str, Any]:
    """
    Admin endpoint to simulate generation of an STS code for a meter via 3rd party (like top-up).
    """
    token = usecase.execute(meter_id, amount=data.amount)
    return {
        "success": True,
        "data": {
            "token": token
        }
    }

