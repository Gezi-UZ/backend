"""
Use Cases do módulo de Recargas.

InitiateRechargeUseCase   — RF03: Cria recarga PENDING, dispara STK Push via E2Payments.
GetRechargeStatusUseCase  — RF03: Consulta estado actual de uma recarga (one-shot).
GetRechargeHistoryUseCase — RF06: Histórico paginado de recargas.
GetRechargeDashboardUseCase — RF14: Estatísticas agregadas.
"""
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.audit.application.usecases.create_audit_log import CreateAuditLogUseCase

from app.modules.recharges.domain.repositories.recharge_repository import IRechargeRepository
from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.recharges.domain.entities.schemas import (
    RechargeInitiateRequest,
    RechargeInitiateResponse,
    RechargeStatusResponse,
    RechargeHistoryResponse,
    RechargeHistoryItem,
    RechargeDashboardResponse,
    PaginationMeta,
    RechargeBreakdownResponse,
)
from app.modules.recharges.domain.services.tariff_calculator import (
    calcular_desdobramento,
    MONTANTE_MINIMO_MZN,
)

logger = logging.getLogger(__name__)


class InitiateRechargeUseCase:
    """
    RF03 — Inicia o processo de recarga.

    Pipeline:
      1. Valida montante mínimo (RN01) e posse do contador (RN09)
      2. Calcula o desdobramento tarifário CREDELEC
      3. Cria registo Recarga com estado PENDING
      4. Resolve o número de telefone (do request ou do perfil do utilizador)
      5. Cria Pagamento e dispara STK Push via E2Payments
      6. Actualiza Recarga para PAYMENT_PROCESSING
      7. Retorna resposta com estado do pagamento
    """

    def __init__(
        self,
        recharge_repo: IRechargeRepository,
        meter_repo: IMeterRepository,
        db: Session,
        audit_usecase: CreateAuditLogUseCase,
    ):
        self.recharge_repo = recharge_repo
        self.meter_repo = meter_repo
        self.db = db
        self.audit_usecase = audit_usecase

    async def execute(
        self, user_id: uuid.UUID, data: RechargeInitiateRequest
    ) -> RechargeInitiateResponse:
        # 1. Validar montante mínimo (RN01)
        if data.amount_mzn < MONTANTE_MINIMO_MZN:
            raise HTTPException(
                status_code=422,
                detail=f"Valor mínimo de recarga é {MONTANTE_MINIMO_MZN} MZN.",
            )

        # 2. Verificar que o contador pertence ao utilizador (RN09)
        meter = self.meter_repo.get_by_id(data.meter_id)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado.")
        if meter.utilizador_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Contador não pertence ao utilizador autenticado.",
            )

        # 3. Verificar se é a primeira compra do mês para este contador (RN — taxas fixas mensais)
        is_primeira_compra_mes = not self.recharge_repo.has_successful_recharge_this_month(
            meter_id=data.meter_id
        )

        # 4. Calcular desdobramento tarifário
        breakdown = calcular_desdobramento(
            montante_total=data.amount_mzn,
            divida_pendente=0.0,  # TODO: integrar com sistema de dívidas EDM
            is_primeira_compra_mes=is_primeira_compra_mes,
        )

        # 5. Criar recarga com estado PENDING
        recharge = self.recharge_repo.create_with_breakdown(
            user_id=user_id,
            meter_id=data.meter_id,
            montante=data.amount_mzn,
            breakdown_data=breakdown,
            is_primeira_compra=is_primeira_compra_mes,
        )

        # 5. Resolver número de telefone para o STK Push
        phone = self._resolve_phone(data.phone, user_id)

        # 6. Disparar STK Push via E2Payments
        payment_status = "INITIATED"
        if phone:
            payment_status = await self._initiate_payment(
                recharge_id=recharge.id,
                user_id=user_id,
                amount=data.amount_mzn,
                phone=phone,
            )
            # Actualizar estado da recarga para PAYMENT_PROCESSING
            if payment_status == "PROCESSING":
                self.recharge_repo.update_status(recharge.id, "PAYMENT_PROCESSING")
        else:
            logger.warning(
                f"Recarga {recharge.id}: Sem telefone disponível para STK Push. "
                "Aguardando reconciliação manual ou callback."
            )

        # 7. Auditar a acção do cliente
        self.audit_usecase.execute(
            accao="RECARGA_CONTADOR",
            entidade="contador",
            entidade_id=str(data.meter_id),
            admin_id=None,
            detalhes=f"Utilizador {user_id} iniciou recarga de {data.amount_mzn} MZN. Recharge ID: {recharge.id}"
        )

        return RechargeInitiateResponse(
            recharge_id=recharge.id,
            status="PAYMENT_PROCESSING" if payment_status == "PROCESSING" else recharge.estado,
            amount_mzn=recharge.montante_pago,
            estimated_kwh=breakdown["kwh_calculado"],
            payment_status=payment_status,
            is_primeira_compra_mes=is_primeira_compra_mes,
            breakdown=RechargeBreakdownResponse(**breakdown),
        )

    def _resolve_phone(self, phone_from_request: Optional[str], user_id: uuid.UUID) -> Optional[str]:
        """
        Resolve o número de telefone para o STK Push.
        Prioridade: campo do request → telefone do perfil do utilizador.
        """
        if phone_from_request:
            return phone_from_request

        # Tentar obter do perfil do utilizador
        try:
            from app.modules.users.domain.entities.user import Utilizador
            user = self.db.query(Utilizador).filter(Utilizador.id == user_id).first()
            if user and user.telefone:
                # O telefone está guardado com 9 dígitos
                return user.telefone
        except Exception as exc:
            logger.warning(f"Não foi possível obter telefone do utilizador {user_id}: {exc}")

        return None

    async def _initiate_payment(
        self,
        recharge_id: uuid.UUID,
        user_id: uuid.UUID,
        amount: float,
        phone: str,
    ) -> str:
        """
        Cria o Pagamento e chama o E2Payments. Retorna o estado resultante.
        Nunca propaga excepções — falha silenciosa com log (a reconciliação trata).
        """
        try:
            from app.modules.payments.application.usecases.payment_service import InitiatePaymentUseCase
            from app.modules.payments.infrastructure.providers.e2payments import E2PaymentsProvider
            from app.core.config import settings

            gateway = E2PaymentsProvider(
                base_url=settings.e2payments_base_url,
                client_id=settings.e2payments_client_id,
                client_secret=settings.e2payments_client_secret,
                wallet_id=settings.e2payments_wallet_id,
            )
            usecase = InitiatePaymentUseCase(db=self.db, gateway=gateway)
            pagamento = await usecase.execute(
                recharge_id=recharge_id,
                user_id=user_id,
                amount=amount,
                phone=phone,
            )
            return pagamento.estado  # "PROCESSING" ou "FAILED"

        except Exception as exc:
            logger.error(f"Erro ao iniciar pagamento para recarga {recharge_id}: {exc}")
            return "FAILED"


class GetRechargeStatusUseCase:
    """RF03 — Consulta o estado de uma recarga em curso."""

    def __init__(self, recharge_repo: IRechargeRepository, meter_repo: IMeterRepository):
        self.recharge_repo = recharge_repo
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID, recharge_id: uuid.UUID) -> RechargeStatusResponse:
        recharge = self.recharge_repo.get_by_id(recharge_id)
        if not recharge:
            raise HTTPException(status_code=404, detail="Recarga não encontrada.")

        # Verificar que o contador da recarga pertence ao utilizador
        meter = self.meter_repo.get_by_id(recharge.contador_id)
        if not meter or meter.utilizador_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado.")

        return RechargeStatusResponse(
            recharge_id=recharge.id,
            status=recharge.estado,
            token=recharge.token_sts,
            applied_at=recharge.recarregado_em,
        )


class GetRechargeHistoryUseCase:
    """RF06 — Histórico de recargas com filtros e paginação."""

    def __init__(self, recharge_repo: IRechargeRepository):
        self.recharge_repo = recharge_repo

    def execute(
        self,
        user_id: uuid.UUID,
        meter_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> RechargeHistoryResponse:
        skip = (page - 1) * page_size
        recharges, total = self.recharge_repo.get_history(
            user_id=user_id,
            meter_id=meter_id,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=page_size,
        )

        items = []
        for r in recharges:
            referencia = None
            if r.pagamentos:
                # Obter a referência do pagamento bem-sucedido ou do último registado
                pag = next((p for p in r.pagamentos if p.estado == 'SUCCESS'), r.pagamentos[-1])
                referencia = pag.referencia_mpesa

            recharge_type = "SELF"
            other_party_name = None
            if r.utilizador_id == user_id and r.contador.utilizador_id != user_id:
                recharge_type = "FOR_OTHER"
                other_party_name = r.contador.utilizador.nome if (r.contador and r.contador.utilizador) else (r.contador.label if r.contador else None)
            elif r.utilizador_id != user_id and r.contador.utilizador_id == user_id:
                recharge_type = "RECEIVED"
                other_party_name = r.utilizador.nome if r.utilizador else "Unknown"

            items.append(
                RechargeHistoryItem(
                    recharge_id=r.id,
                    meter_id=r.contador_id,
                    meter_serial_number=r.contador.numero_serie if r.contador else None,
                    amount_mzn=r.montante_pago,
                    credit_kwh=r.kwh_creditado,
                    status=r.estado,
                    created_at=r.criado_em,
                    payment_method=r.metodo,
                    referencia_mpesa=referencia,
                    recharge_type=recharge_type,
                    other_party_name=other_party_name,
                )
            )

        return RechargeHistoryResponse(
            recharges=items,
            pagination=PaginationMeta(page=page, page_size=page_size, total=total),
        )


class GetRechargeDashboardUseCase:
    """RF14 — Estatísticas agregadas de consumo."""

    def __init__(self, recharge_repo: IRechargeRepository):
        self.recharge_repo = recharge_repo

    def execute(
        self,
        user_id: uuid.UUID,
        meter_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> RechargeDashboardResponse:
        stats = self.recharge_repo.get_dashboard_stats(
            user_id=user_id,
            meter_id=meter_id,
            from_date=from_date,
            to_date=to_date,
        )
        return RechargeDashboardResponse(**stats)
