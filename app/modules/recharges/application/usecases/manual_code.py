import uuid
import re
from datetime import datetime, timezone

from fastapi import HTTPException

from app.modules.recharges.domain.repositories.recharge_repository import IRechargeRepository
from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.recharges.domain.entities.schemas import ManualCodeRequest, ManualCodeResponse
from app.modules.recharges.domain.services.tariff_calculator import calcular_desdobramento

# Formato CREDELEC: 4 grupos de 4 dígitos separados por hífen
_CREDELEC_CODE_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{4}$")


class ApplyManualCodeUseCase:
    """
    RF16, RN10 — Aplica um código de recarga CREDELEC obtido por canal externo.

    Validações:
    - Formato do código (4x4 dígitos com hífenes)
    - Uso único (RN10): 409 se o código já foi aplicado
    - Pertença do contador ao utilizador (RN09)
    """

    def __init__(self, recharge_repo: IRechargeRepository, meter_repo: IMeterRepository):
        self.recharge_repo = recharge_repo
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID, data: ManualCodeRequest) -> ManualCodeResponse:
        # 1. Validar formato do código
        if not _CREDELEC_CODE_PATTERN.match(data.recharge_code):
            raise HTTPException(
                status_code=422,
                detail="Código inválido. Formato esperado: XXXX-XXXX-XXXX-XXXX (apenas dígitos)."
            )

        # 2. Verificar uso único (RN10) — 409 se já utilizado
        existing = self.recharge_repo.get_by_meter_and_code(data.recharge_code)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Este código já foi utilizado anteriormente (RN10)."
            )

        # 3. Verificar que o contador pertence ao utilizador (RN09)
        meter = self.meter_repo.get_by_id(data.meter_id)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado.")
        if meter.utilizador_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Contador não pertence ao utilizador autenticado."
            )

        # 4. Calcular kWh estimado (usando valor de referência — código externo não tem montante associado)
        # Para códigos manuais, usamos o kwh_creditado do token (fixo por tipo de código)
        # Em produção, o backend consultaria a API CREDELEC para obter o valor em kWh
        # Por agora, usamos um cálculo baseado num montante padrão de 200 MZN
        MONTANTE_PADRAO = 200.0
        breakdown = calcular_desdobramento(montante_total=MONTANTE_PADRAO)
        credit_kwh = breakdown["kwh_calculado"]

        # 5. Criar registo da recarga com o token e enviá-la directamente para MQTT_SENT
        recharge = self.recharge_repo.create_with_breakdown(
            meter_id=data.meter_id,
            montante=MONTANTE_PADRAO,
            breakdown_data=breakdown,
            metodo="MANUAL_CODE",
        )

        # 6. Gravar o token no registo (marcando como já utilizado — RN10)
        now = datetime.now(timezone.utc)
        recharge = self.recharge_repo.update_token(recharge.id, data.recharge_code, now)

        # Actualizar estado para MQTT_SENT (o código será publicado via MQTT pelo caller)
        recharge = self.recharge_repo.update_status(recharge.id, "MQTT_SENT")

        return ManualCodeResponse(
            recharge_id=recharge.id,
            status=recharge.estado,
            credit_kwh=credit_kwh,
        )
