from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.meters.domain.entities.schemas import MeterResponse
from app.modules.meters.presentation.dependencies import get_list_all_meters_usecase
from app.modules.meters.application.usecases.list_all_meters import ListAllMetersUseCase

router = APIRouter()

@router.get("/meters")
def list_all_meters(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: ListAllMetersUseCase = Depends(get_list_all_meters_usecase)
) -> Dict[str, Any]:
    """
    Admin endpoint to list all meters in the system.
    """
    meters = usecase.execute(status=status, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "meters": [MeterResponse.model_validate(m).model_dump(by_alias=True) for m in meters]
        }
    }
