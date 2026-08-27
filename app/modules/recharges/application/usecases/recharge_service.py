import uuid
import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

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


def _gerar_token_sts() -> str:
    """Gera um token STS CREDELEC no formato XXXX-XXXX-XXXX-XXXX."""
    digits = string.digits
    grupos = [
        "".join(secrets.choice(digits) for _ in range(4))
        for _ in range(4)
    ]
    return "-".join(grupos)


class InitiateRechargeUseCase:
    """
    RF03 — Inicia o processo de recarga.
    Cria registo PENDING, calcula o desdobramento tarifário CREDELEC
    e devolve o montante estimado em kWh.
    """

    def __init__(self, recharge_repo: IRechargeRepository, meter_repo: IMeterRepository):
        self.recharge_repo = recharge_repo
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID, data: RechargeInitiateRequest) -> RechargeInitiateResponse:
        # Validar montante mínimo (RN01)
        if data.amount_mzn < MONTANTE_MINIMO_MZN:
            raise HTTPException(
                status_code=422,
                detail=f"Valor mínimo de recarga é {MONTANTE_MINIMO_MZN} MZN."
            )

        # Verificar que o contador pertence ao utilizador (RN09)
        meter = self.meter_repo.get_by_id(data.meter_id)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado.")
        if meter.utilizador_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Contador não pertence ao utilizador autenticado."
            )

        # Calcular desdobramento tarifário
        breakdown = calcular_desdobramento(
            montante_total=data.amount_mzn,
            divida_pendente=0.0,  # TODO: integrar com sistema de dívidas EDM
            is_primeira_compra_mes=False,  # TODO: verificar histórico do mês
        )

        # Criar recarga com estado PENDING
        recharge = self.recharge_repo.create_with_breakdown(
            meter_id=data.meter_id,
            montante=data.amount_mzn,
            breakdown_data=breakdown,
        )

        return RechargeInitiateResponse(
            recharge_id=recharge.id,
            status=recharge.estado,
            amount_mzn=recharge.montante_pago,
            estimated_kwh=breakdown["kwh_calculado"],
            breakdown=RechargeBreakdownResponse(**breakdown),
        )


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

        items = [
            RechargeHistoryItem(
                recharge_id=r.id,
                meter_id=r.contador_id,
                amount_mzn=r.montante_pago,
                credit_kwh=r.kwh_creditado,
                status=r.estado,
                created_at=r.criado_em,
            )
            for r in recharges
        ]

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
