import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query

from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.recharges.domain.entities.schemas import (
    RechargeInitiateRequest,
    ManualCodeRequest,
)
from app.modules.recharges.presentation.dependencies import (
    get_initiate_recharge_usecase,
    get_recharge_status_usecase,
    get_recharge_history_usecase,
    get_recharge_dashboard_usecase,
    get_apply_manual_code_usecase,
)
from app.modules.recharges.application.usecases.recharge_service import (
    InitiateRechargeUseCase,
    GetRechargeStatusUseCase,
    GetRechargeHistoryUseCase,
    GetRechargeDashboardUseCase,
)
from app.modules.recharges.application.usecases.manual_code import ApplyManualCodeUseCase

router = APIRouter()


@router.post("/initiate", status_code=201)
def initiate_recharge(
    data: RechargeInitiateRequest,
    current_user: AuthUser = Depends(get_current_user),
    usecase: InitiateRechargeUseCase = Depends(get_initiate_recharge_usecase),
) -> Dict[str, Any]:
    """
    RF03 — Inicia o processo de recarga (cria registo PENDING antes do pagamento).
    """
    result = usecase.execute(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/{recharge_id}/status")
def get_recharge_status(
    recharge_id: uuid.UUID,
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeStatusUseCase = Depends(get_recharge_status_usecase),
) -> Dict[str, Any]:
    """RF03 — Consulta o estado de uma recarga em curso."""
    result = usecase.execute(current_user.id, recharge_id)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/manual-code")
def apply_manual_code(
    data: ManualCodeRequest,
    current_user: AuthUser = Depends(get_current_user),
    usecase: ApplyManualCodeUseCase = Depends(get_apply_manual_code_usecase),
) -> Dict[str, Any]:
    """
    RF16, RN10 — Aplica um código de recarga CREDELEC obtido por canal externo.
    Retorna 409 se o código já foi utilizado anteriormente.
    """
    result = usecase.execute(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/history")
def get_recharge_history(
    meter_id: Optional[uuid.UUID] = Query(None, description="Filtrar por contador"),
    from_date: Optional[datetime] = Query(None, alias="from", description="Data início (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, alias="to", description="Data fim (ISO 8601)"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeHistoryUseCase = Depends(get_recharge_history_usecase),
) -> Dict[str, Any]:
    """RF06 — Histórico de recargas com filtros e paginação."""
    result = usecase.execute(
        user_id=current_user.id,
        meter_id=meter_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/dashboard")
def get_recharge_dashboard(
    meter_id: Optional[uuid.UUID] = Query(None, description="Filtrar por contador"),
    period: Optional[str] = Query("month", description="Período: week | month | year"),
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetRechargeDashboardUseCase = Depends(get_recharge_dashboard_usecase),
) -> Dict[str, Any]:
    """RF14 — Estatísticas agregadas de consumo."""
    # Calcular datas com base no período
    from datetime import timedelta
    now = datetime.utcnow()
    period_map = {
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "year": timedelta(days=365),
    }
    delta = period_map.get(period, timedelta(days=30))
    from_date = now - delta

    result = usecase.execute(
        user_id=current_user.id,
        meter_id=meter_id,
        from_date=from_date,
        to_date=now,
    )
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
