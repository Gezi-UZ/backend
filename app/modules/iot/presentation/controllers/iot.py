"""
Controller IoT — Endpoints para envio de comandos ao ESP32 e callback de pagamento.
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.mqtt import publish_command
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.meters.domain.entities.meter import Contador
from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from app.modules.iot.domain.entities.schemas import (
    IoTCommandRequest,
    IoTCommandResponse,
    PaymentCallbackRequest,
)
from app.modules.recharges.application.usecases.confirm_payment import ConfirmPaymentUseCase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/meters/{meter_id}/command", response_model=IoTCommandResponse, status_code=201)
def send_iot_command(
    meter_id: uuid.UUID,
    data: IoTCommandRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IoTCommandResponse:
    """
    Envia um comando ao ESP32 de um contador especifico via MQTT.

    Comandos disponiveis:
    - APPLY_CREDITS: Aplica um token STS gerado por recarga
    - CUT_SUPPLY: Corta o fornecimento de energia (rele)
    - RESTORE_SUPPLY: Restaura o fornecimento de energia (rele)
    - STATUS_REQUEST: Solicita telemetria imediata
    """
    # Verificar se o contador pertence ao utilizador
    contador = (
        db.query(Contador)
        .filter(Contador.id == meter_id, Contador.utilizador_id == current_user.id)
        .first()
    )

    if not contador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contador nao encontrado ou nao pertence ao utilizador",
        )

    if not contador.dispositivo_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Contador sem dispositivo IoT associado",
        )

    # Criar registo de comando na BD
    comando = ComandoIoT(
        id=uuid.uuid4(),
        tipo=data.command_type,
        estado="ENVIADO",
        hmac_token="",
        dispositivo_id=contador.dispositivo_id,
        recarga_id=None,
    )
    db.add(comando)
    db.commit()

    # Publicar comando via MQTT
    publish_command(
        meter_serial=contador.numero_serie,
        command_type=data.command_type,
        payload={
            "command_id": str(comando.id),
            **data.payload,
        },
    )

    logger.info(f"IoT: Comando '{data.command_type}' enviado para contador '{contador.numero_serie}'")

    return IoTCommandResponse(
        command_id=comando.id,
        meter_id=meter_id,
        command_type=data.command_type,
        status="ENVIADO",
        sent_at=datetime.utcnow(),
    )


@router.post("/payments/callback")
def mpesa_payment_callback(
    data: PaymentCallbackRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Callback do M-Pesa — Recebe confirmacao de pagamento.

    Este endpoint eh chamado pela integracao M-Pesa quando um pagamento
    eh confirmado. Dispara o pipeline completo:
    Pagamento → BD → Comando MQTT → SSE → ESP32.

    NOTA: Este endpoint NAO requer JWT (chamado pelo M-Pesa server-to-server).
    Em producao, validar a assinatura/IP do M-Pesa.
    """
    if data.estado != "SUCCESS":
        logger.info(f"M-Pesa callback: Pagamento '{data.referencia_mpesa}' com estado '{data.estado}' (ignorado)")
        return {"success": True, "message": "Pagamento nao confirmado, ignorado"}

    usecase = ConfirmPaymentUseCase(db)
    result = usecase.execute(data.referencia_mpesa)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Erro ao confirmar pagamento"),
        )

    return {
        "success": True,
        "data": result,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
