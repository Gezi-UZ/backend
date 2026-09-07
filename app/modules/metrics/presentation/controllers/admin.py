from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.metrics.infrastructure.repositories.metrics_repository import MetricsRepository
from app.modules.metrics.application.usecases.get_global_metrics import GetGlobalMetricsUseCase
from app.modules.metrics.application.usecases.get_metrics_history import GetMetricsHistoryUseCase
from datetime import datetime

router = APIRouter()

def get_metrics_repo(db: Session = Depends(get_db)):
    return MetricsRepository(db)

def get_global_metrics_usecase(repo: MetricsRepository = Depends(get_metrics_repo)):
    return GetGlobalMetricsUseCase(repo)

def get_history_usecase(db: Session = Depends(get_db)):
    return GetMetricsHistoryUseCase(db)

@router.get("/metrics")
def get_global_metrics(
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: GetGlobalMetricsUseCase = Depends(get_global_metrics_usecase)
) -> Dict[str, Any]:
    """
    Obtém as métricas globais para o dashboard administrativo.
    """
    result = usecase.execute()
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@router.get("/metrics/history")
def get_metrics_history(
    period: str = Query("7d", description="Período de histórico (ex: 7d, 30d)"),
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: GetMetricsHistoryUseCase = Depends(get_history_usecase)
) -> Dict[str, Any]:
    """
    Obtém o histórico de receitas e transacções.
    """
    result = usecase.execute(period=period)
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
