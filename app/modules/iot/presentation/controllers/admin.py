from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.core.mqtt import publish_command
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.iot.presentation.dependencies import get_list_iot_devices_usecase
from app.modules.iot.application.usecases.list_iot_devices import ListIoTDevicesUseCase
from app.modules.iot.domain.entities.schemas import IoTCommandRequest, IoTCommandResponse
from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from app.modules.iot.domain.entities.iot import DispositivoIoT
from app.modules.meters.domain.entities.meter import Contador
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/iot-modules")
def get_iot_modules(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: ListIoTDevicesUseCase = Depends(get_list_iot_devices_usecase)
) -> Dict[str, Any]:
    """
    Lista todos os módulos IoT do sistema (Apenas Admin).
    """
    skip = (page - 1) * page_size
    result = usecase.execute(skip=skip, limit=page_size)
    
    return {
        "success": True,
        "data": result.model_dump(),
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@router.post("/iot-modules/{device_id}/command", response_model=IoTCommandResponse)
def admin_send_iot_command(
    device_id: uuid.UUID,
    data: IoTCommandRequest,
    admin_user: AuthUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> IoTCommandResponse:
    """
    Envia um comando administrativo ao ESP32 via MQTT (Ex: REBOOT, OTA_UPDATE).
    """
    device = db.query(DispositivoIoT).filter(DispositivoIoT.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Módulo IoT não encontrado",
        )
        
    contador = db.query(Contador).filter(Contador.dispositivo_id == device_id).first()
    meter_serial = contador.numero_serie if contador else device.mac_address

    comando = ComandoIoT(
        id=uuid.uuid4(),
        tipo=data.command_type,
        estado="ENVIADO",
        hmac_token="",
        dispositivo_id=device.id,
        recarga_id=None,
    )
    db.add(comando)
    db.commit()

    publish_command(
        meter_serial=meter_serial,
        command_type=data.command_type,
        payload={
            "command_id": str(comando.id),
            **data.payload,
        },
    )

    logger.info(f"IoT Admin: Comando '{data.command_type}' enviado para dispositivo '{device.id}'")

    return IoTCommandResponse(
        command_id=comando.id,
        meter_id=contador.id if contador else uuid.uuid4(), # Fallback if no meter
        command_type=data.command_type,
        status="ENVIADO",
        sent_at=datetime.utcnow(),
    )
