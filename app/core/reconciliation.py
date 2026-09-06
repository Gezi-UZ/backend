"""
Background Task de Reconciliação de Pagamentos — Safety Net (Opção C).

Corre a cada 30 segundos no lifespan do FastAPI.
Chama o ReconcilePaymentsUseCase para detectar pagamentos confirmados
no E2Payments que ainda não foram processados localmente.

Este é o "safety net" da Opção C: garante que mesmo que o Flutter
desconecte antes de o pagamento ser confirmado, o pipeline avança.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

_RECONCILE_INTERVAL_SECONDS = 30


async def reconciliation_task():
    """
    Task de background que roda indefinidamente, reconciliando pagamentos a cada 30s.
    Iniciada no lifespan do FastAPI (app/main.py).
    """
    # Aguarda 10s no arranque para dar tempo ao servidor de inicializar
    await asyncio.sleep(10)
    logger.info("Reconciliação: Background task iniciada (intervalo: 30s)")

    while True:
        try:
            await _run_reconciliation()
        except Exception as exc:
            logger.error(f"Reconciliação: Erro inesperado na task: {exc}")

        await asyncio.sleep(_RECONCILE_INTERVAL_SECONDS)


async def _run_reconciliation():
    """Executa um ciclo de reconciliação."""
    from app.modules.payments.application.usecases.payment_service import ReconcilePaymentsUseCase
    from app.modules.payments.infrastructure.providers.e2payments import E2PaymentsProvider
    from app.core.config import settings
    from app.core.database import SessionLocal

    # Verificar se as credenciais estão configuradas (evita spam de logs se .env estiver vazio)
    if not settings.e2payments_client_id or not settings.e2payments_client_secret:
        logger.debug("Reconciliação: Credenciais E2Payments não configuradas — a saltar.")
        return

    gateway = E2PaymentsProvider(
        base_url=settings.e2payments_base_url,
        client_id=settings.e2payments_client_id,
        client_secret=settings.e2payments_client_secret,
        wallet_id=settings.e2payments_wallet_id,
    )

    db = SessionLocal()
    try:
        usecase = ReconcilePaymentsUseCase(db=db, gateway=gateway)
        stats = await usecase.execute(limit=20)
        if stats.get("confirmados", 0) > 0:
            logger.info(f"Reconciliação (safety net): {stats}")
    finally:
        db.close()
