import uuid
import re
from datetime import datetime, timezone

from fastapi import HTTPException

from app.modules.recharges.domain.repositories.recharge_repository import IRechargeRepository
from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.recharges.domain.entities.schemas import ManualCodeRequest, ManualCodeResponse
from app.modules.recharges.domain.services.tariff_calculator import calcular_desdobramento
from app.modules.notifications.application.notification_service import NotificationService

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

    def __init__(self, recharge_repo: IRechargeRepository, meter_repo: IMeterRepository, db=None):
        self.recharge_repo = recharge_repo
        self.meter_repo = meter_repo
        self.notification_service = NotificationService(db) if db else None

    def execute(self, user_id: uuid.UUID, data: ManualCodeRequest) -> ManualCodeResponse:
        # 1. Validar formato do código
        if not _CREDELEC_CODE_PATTERN.match(data.recharge_code):
            raise HTTPException(
                status_code=422,
                detail="Código inválido. Formato esperado: XXXX-XXXX-XXXX-XXXX (apenas dígitos)."
            )

        # 2. Procurar a recarga associada a este código STS
        existing_recharge = self.recharge_repo.get_by_meter_and_code(data.recharge_code)
        if not existing_recharge:
            raise HTTPException(
                status_code=404,
                detail="Código de recarga não encontrado."
            )

        # 3. Verificar uso único (RN10) — 409 se já utilizado
        if existing_recharge.token_sts_usado:
            raise HTTPException(
                status_code=409,
                detail="Este código já foi utilizado anteriormente (RN10)."
            )

        # 4. Verificar que o contador pertence ao utilizador (RN09)
        meter = existing_recharge.contador
        if not meter or meter.utilizador_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Este código não pertence a nenhum dos seus contadores."
            )

        # 5. Marcar token como usado e actualizar estado para MQTT_SENT
        now = datetime.now(timezone.utc)
        updated_recharge = self.recharge_repo.mark_token_used(existing_recharge.id, now)

        # 6. Notificar o utilizador
        if self.notification_service:
            try:
                self.notification_service.notify_manual_code_success(
                    user_id=user_id,
                    recharge_id=updated_recharge.id,
                    kwh=updated_recharge.kwh_creditado or 0.0,
                    meter_number=meter.numero_serie,
                )
            except Exception as _e:
                import logging
                logging.getLogger(__name__).error(
                    f"ApplyManualCode: Erro ao criar notificação: {_e}"
                )

        return ManualCodeResponse(
            recharge_id=updated_recharge.id,
            status=updated_recharge.estado,
            credit_kwh=updated_recharge.kwh_creditado or 0.0,
            meter_number=meter.numero_serie,
        )
