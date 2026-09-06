"""
Use Cases do módulo de Pagamentos.

InitiatePaymentUseCase  — Dispara o STK Push via E2Payments e cria o registo Pagamento.
ReconcilePaymentsUseCase — Consulta o E2Payments e confirma pagamentos ainda pendentes.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.payments.domain.entities.payment import Pagamento
from app.modules.payments.domain.repositories.payment_gateway import IPaymentGateway

logger = logging.getLogger(__name__)


class InitiatePaymentUseCase:
    """
    Cria um registo Pagamento na BD e dispara o STK Push via E2Payments.

    Fluxo:
      1. Cria Pagamento com estado=INITIATED e a referência GEZI-<uuid_short>
      2. Chama gateway.initiate_c2b()
      3. Se sucesso → estado=PROCESSING
      4. Se erro    → estado=FAILED (não propaga — a recarga continua em PAYMENT_PROCESSING
                       para ser reconciliada pelo polling se necessário)
    """

    def __init__(self, db: Session, gateway: IPaymentGateway):
        self.db = db
        self.gateway = gateway

    async def execute(
        self,
        recharge_id: uuid.UUID,
        user_id: uuid.UUID,
        amount: float,
        phone: str,
    ) -> Pagamento:
        # Gera referência única sem espaços (GEZI-<8 chars do uuid>)
        short_id = str(recharge_id).replace("-", "")[:8].upper()
        reference = f"GEZI-{short_id}"

        # Cria registo na BD
        pagamento = Pagamento(
            id=uuid.uuid4(),
            referencia_mpesa=reference,
            montante=amount,
            estado="INITIATED",
            recarga_id=recharge_id,
            utilizador_id=user_id,
        )
        self.db.add(pagamento)
        self.db.commit()
        self.db.refresh(pagamento)

        logger.info(f"Pagamento criado: {pagamento.id} | ref={reference} | amount={amount} | phone={phone}")

        # Disparar STK Push
        result = await self.gateway.initiate_c2b(
            amount=amount,
            phone=phone,
            reference=reference,
        )

        if result.success:
            pagamento.estado = "PROCESSING"
            logger.info(f"Pagamento {pagamento.id}: STK Push enviado com sucesso | ref={reference}")
        else:
            pagamento.estado = "FAILED"
            logger.error(f"Pagamento {pagamento.id}: Falha no STK Push | {result.error_message}")

        self.db.commit()
        return pagamento


class ReconcilePaymentsUseCase:
    """
    Reconcilia pagamentos pendentes consultando o histórico do E2Payments.

    Como o E2Payments não tem webhooks, este use case é chamado:
    - Periodicamente pelo background task (cada 30s — safety net)
    - A cada 5s durante o SSE stream ativo de uma recarga

    Para cada pagamento confirmado no gateway com referência GEZI-*,
    se ainda não foi confirmado localmente, dispara o ConfirmPaymentUseCase.
    """

    def __init__(self, db: Session, gateway: IPaymentGateway):
        self.db = db
        self.gateway = gateway

    async def execute(self, limit: int = 20) -> dict:
        """
        Reconcilia os pagamentos recentes.

        Returns:
            Dicionário com estatísticas: total consultado, confirmados, já processados, erros.
        """
        stats = {"consultados": 0, "confirmados": 0, "ja_processados": 0, "erros": 0}

        # Consultar E2Payments
        confirmed_payments = await self.gateway.get_recent_confirmed_payments(limit=limit)
        stats["consultados"] = len(confirmed_payments)

        if not confirmed_payments:
            return stats

        # Importação tardia para evitar importação circular
        from app.modules.recharges.application.usecases.confirm_payment import ConfirmPaymentUseCase

        confirm_usecase = ConfirmPaymentUseCase(self.db)

        for payment_status in confirmed_payments:
            ref = payment_status.reference

            # Só interessa referências geradas pelo Gezi
            if not ref.startswith("GEZI-"):
                continue

            # Verificar se já está confirmado localmente
            pagamento = (
                self.db.query(Pagamento)
                .filter(Pagamento.referencia_mpesa == ref)
                .first()
            )

            if not pagamento:
                logger.debug(f"Reconciliação: referência '{ref}' não encontrada na BD local")
                continue

            if pagamento.estado == "SUCCESS":
                stats["ja_processados"] += 1
                continue

            # Confirmar pagamento e disparar pipeline
            logger.info(f"Reconciliação: Confirmando pagamento '{ref}' (estado actual: {pagamento.estado})")
            result = confirm_usecase.execute(ref)

            if result.get("success"):
                stats["confirmados"] += 1
            else:
                stats["erros"] += 1
                logger.warning(f"Reconciliação: Falha ao confirmar '{ref}': {result.get('error')}")

        if stats["confirmados"] > 0 or stats["erros"] > 0:
            logger.info(f"Reconciliação concluída: {stats}")

        return stats
