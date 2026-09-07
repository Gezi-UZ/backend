from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.recharges.presentation.dependencies import get_list_admin_transactions_usecase
from app.modules.recharges.application.usecases.admin_transactions import ListAdminTransactionsUseCase

router = APIRouter()

@router.get("/transactions")
def get_transactions(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    from_date: Optional[datetime] = Query(None, alias="from", description="Data de início"),
    to_date: Optional[datetime] = Query(None, alias="to", description="Data de fim"),
    meter_id: Optional[uuid.UUID] = Query(None, description="Filtrar por contador_id"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: ListAdminTransactionsUseCase = Depends(get_list_admin_transactions_usecase)
) -> Dict[str, Any]:
    """
    Lista transacções/recargas com detalhes de utilizador e método de pagamento (Apenas Admin).
    """
    result = usecase.execute(
        status=status,
        from_date=from_date,
        to_date=to_date,
        meter_id=meter_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
