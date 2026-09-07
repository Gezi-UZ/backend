from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.audit.presentation.dependencies import get_list_audit_logs_usecase
from app.modules.audit.application.usecases.list_audit_logs import ListAuditLogsUseCase
from datetime import datetime

router = APIRouter()

@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: ListAuditLogsUseCase = Depends(get_list_audit_logs_usecase)
) -> Dict[str, Any]:
    """
    Lista os registos de auditoria do sistema (Apenas Admin).
    """
    result = usecase.execute(page=page, page_size=page_size)
    
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
