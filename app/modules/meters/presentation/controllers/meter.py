from fastapi import APIRouter, Depends
from typing import List, Dict, Any
import uuid
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.meters.domain.entities.schemas import MeterCreate, MeterUpdate, MeterResponse, MeterStatusResponse
from app.modules.meters.presentation.dependencies import (
    get_register_meter_usecase,
    get_list_my_meters_usecase,
    get_get_meter_usecase,
    get_update_meter_usecase,
    get_get_meter_status_usecase
)
from app.modules.meters.application.usecases.register_meter import RegisterMeterUseCase
from app.modules.meters.application.usecases.list_my_meters import ListMyMetersUseCase
from app.modules.meters.application.usecases.get_meter import GetMeterUseCase
from app.modules.meters.application.usecases.update_meter import UpdateMeterUseCase
from app.modules.meters.application.usecases.get_meter_status import GetMeterStatusUseCase

router = APIRouter()

@router.get("/me")
def list_my_meters(
    current_user: AuthUser = Depends(get_current_user),
    usecase: ListMyMetersUseCase = Depends(get_list_my_meters_usecase)
) -> Dict[str, Any]:
    meters = usecase.execute(current_user.id)
    return {
        "success": True,
        "data": {
            "meters": [MeterResponse.model_validate(m).model_dump(by_alias=True) for m in meters]
        }
    }

@router.post("/", status_code=201)
def register_meter(
    meter_data: MeterCreate,
    current_user: AuthUser = Depends(get_current_user),
    usecase: RegisterMeterUseCase = Depends(get_register_meter_usecase)
) -> Dict[str, Any]:
    meter = usecase.execute(current_user.id, meter_data)
    return {
        "success": True,
        "data": {
            "meter_id": str(meter.id),
            "status": meter.estado
        }
    }

@router.get("/{meter_id}")
def get_meter(
    meter_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetMeterUseCase = Depends(get_get_meter_usecase)
) -> Dict[str, Any]:
    meter = usecase.execute(current_user.id, meter_id)
    return {
        "success": True,
        "data": MeterResponse.model_validate(meter).model_dump(by_alias=True)
    }

@router.patch("/{meter_id}")
def update_meter(
    meter_id: uuid.UUID,
    meter_update: MeterUpdate,
    current_user: AuthUser = Depends(get_current_user),
    usecase: UpdateMeterUseCase = Depends(get_update_meter_usecase)
) -> Dict[str, Any]:
    usecase.execute(current_user.id, meter_id, meter_update)
    return {
        "success": True,
        "data": {
            "meter_id": str(meter_id),
            "updated": True
        }
    }

@router.get("/{meter_id}/status")
def get_meter_status(
    meter_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetMeterStatusUseCase = Depends(get_get_meter_status_usecase)
) -> Dict[str, Any]:
    meter = usecase.execute(current_user.id, meter_id)
    return {
        "success": True,
        "data": MeterStatusResponse.model_validate(meter).model_dump(by_alias=True)
    }
