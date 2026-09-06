"""
Controller de Pagamentos — Endpoint admin para reconciliação manual.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/e2p/reconcile")
async def force_reconcile(
    limit: int = 20,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Admin — Força uma reconciliação imediata com o E2Payments.

    Útil para suporte e debug. Consulta os últimos `limit` pagamentos
    no E2Payments e confirma os que ainda estão pendentes localmente.

    Requer utilizador autenticado (em produção, restringir a papel=admin).
    """
    from app.modules.payments.application.usecases.payment_service import ReconcilePaymentsUseCase
    from app.modules.payments.infrastructure.providers.e2payments import E2PaymentsProvider
    from app.core.config import settings

    if not settings.e2payments_client_id:
        raise HTTPException(
            status_code=503,
            detail="Credenciais E2Payments não configuradas.",
        )

    gateway = E2PaymentsProvider(
        base_url=settings.e2payments_base_url,
        client_id=settings.e2payments_client_id,
        client_secret=settings.e2payments_client_secret,
        wallet_id=settings.e2payments_wallet_id,
    )
    usecase = ReconcilePaymentsUseCase(db=db, gateway=gateway)
    stats = await usecase.execute(limit=limit)

    logger.info(f"Reconciliação manual por {current_user.id}: {stats}")

    return {
        "success": True,
        "data": stats,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/e2p/wallets")
async def list_e2p_wallets(
    current_user: AuthUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Admin — Lista as carteiras Mpesa configuradas no E2Payments.
    Útil para verificar se o wallet_id está correcto.
    """
    from app.modules.payments.infrastructure.providers.e2payments import E2PaymentsProvider
    from app.core.config import settings

    if not settings.e2payments_client_id:
        raise HTTPException(status_code=503, detail="Credenciais E2Payments não configuradas.")

    gateway = E2PaymentsProvider(
        base_url=settings.e2payments_base_url,
        client_id=settings.e2payments_client_id,
        client_secret=settings.e2payments_client_secret,
        wallet_id=settings.e2payments_wallet_id,
    )
    wallets = await gateway.list_wallets()

    return {
        "success": wallets is not None,
        "data": wallets,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
