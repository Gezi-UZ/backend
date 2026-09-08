from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.core.mqtt import publish_command
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.iot.presentation.dependencies import get_list_iot_devices_usecase
from app.modules.iot.application.usecases.list_iot_devices import ListIoTDevicesUseCase
from app.modules.iot.domain.entities.schemas import IoTCommandRequest, IoTCommandResponse, BindMetersRequest
from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from app.modules.iot.domain.entities.iot import DispositivoIoT
from app.modules.meters.domain.entities.meter import Contador
from datetime import datetime
import uuid
import logging
import json
from app.core.mqtt import mqtt_client
from app.modules.audit.presentation.dependencies import log_admin_action

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

@router.post("/iot-modules/{device_id}/bind-meters", status_code=200)
def bind_meters_to_device(
    device_id: uuid.UUID,
    data: BindMetersRequest,
    admin_user: AuthUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Vincula os contadores aos Canais 0 e 1 do módulo físico IoT.
    Atualiza a BD e envia imediatamente a configuração via MQTT para o ESP32.
    """
    device = db.query(DispositivoIoT).filter(DispositivoIoT.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Módulo IoT não encontrado")

    contador_c0 = db.query(Contador).filter(Contador.numero_serie == data.meter_serial_c0).first()
    if not contador_c0:
        raise HTTPException(
            status_code=404, 
            detail=f"Contador com série '{data.meter_serial_c0}' não existe no sistema"
        )

    contador_c1 = db.query(Contador).filter(Contador.numero_serie == data.meter_serial_c1).first()
    if not contador_c1:
        raise HTTPException(
            status_code=404, 
            detail=f"Contador com série '{data.meter_serial_c1}' não existe no sistema"
        )

    db.query(Contador).filter(Contador.dispositivo_id == device.id).update(
        {"dispositivo_id": None, "canal": 0}
    )

    contador_c0.dispositivo_id = device.id
    contador_c0.canal = 0

    contador_c1.dispositivo_id = device.id
    contador_c1.canal = 1

    device.estado = "ACTIVE"
    db.commit()

    config_payload = {
        "meter_serial_c0": contador_c0.numero_serie,
        "meter_serial_c1": contador_c1.numero_serie,
    }
    config_topic = f"gezi/v1/{device.mac_address}/config"
    mqtt_client.publish(config_topic, json.dumps(config_payload), qos=1)

    logger.info(
        f"Admin: Dispositivo {device.mac_address} vinculado a C0={contador_c0.numero_serie}, C1={contador_c1.numero_serie}"
    )

    log_admin_action(
        db=db,
        admin_id=admin_user.id,
        accao="VINCULAR_DISPOSITIVO_IOT",
        entidade="dispositivo_iot",
        entidade_id=str(device.id),
        detalhes=f"Vinculado a C0={contador_c0.numero_serie} e C1={contador_c1.numero_serie}"
    )

    return {
        "success": True,
        "message": "Contadores vinculados com sucesso e configuração enviada ao dispositivo.",
        "data": {
            "mac_address": device.mac_address,
            "meter_serial_c0": contador_c0.numero_serie,
            "meter_serial_c1": contador_c1.numero_serie,
        }
    }
