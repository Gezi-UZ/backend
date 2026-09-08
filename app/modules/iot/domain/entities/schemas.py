"""
Schemas Pydantic para o modulo IoT.
"""
from pydantic import BaseModel, Field
import uuid
from typing import Optional
from datetime import datetime


class IoTCommandRequest(BaseModel):
    """Payload enviado pelo Flutter para executar um comando no ESP32."""
    command_type: str = Field(
        ...,
        description="Tipo de comando: APPLY_CREDITS, CUT_SUPPLY, RESTORE_SUPPLY, STATUS_REQUEST"
    )
    payload: dict = Field(
        default_factory=dict,
        description="Dados adicionais para o comando"
    )


class IoTCommandResponse(BaseModel):
    """Resposta apos envio de um comando IoT."""
    command_id: uuid.UUID
    meter_id: uuid.UUID
    command_type: str
    status: str
    sent_at: datetime


class MeterTelemetryResponse(BaseModel):
    """Estado do contador baseado na telemetria mais recente."""
    meter_id: uuid.UUID
    serial_number: str
    kwh_balance: float
    relay_state: bool
    is_online: bool
    last_sync: Optional[datetime] = None


class PaymentCallbackRequest(BaseModel):
    """Payload recebido do callback M-Pesa."""
    referencia_mpesa: str = Field(..., description="Referencia unica da transacao M-Pesa")
    estado: str = Field(default="SUCCESS", description="Estado do pagamento: SUCCESS, FAILED")

class IoTAdminDeviceResponse(BaseModel):
    id: uuid.UUID
    mac_address: str
    firmware_version: Optional[str] = None
    estado: str
    ultimo_heartbeat: Optional[datetime] = None
    meter_id: Optional[uuid.UUID] = None
    meter_serial: Optional[str] = None
    
    class Config:
        from_attributes = True

from pydantic import BaseModel, Field, field_validator

class IoTAdminDeviceListResponse(BaseModel):
    devices: list[IoTAdminDeviceResponse]
    total: int

class BindMetersRequest(BaseModel):
    meter_serial_c0: str = Field(..., description="Serial decimal do Canal 0 (até 11 dígitos)")
    meter_serial_c1: str = Field(..., description="Serial decimal do Canal 1 (até 11 dígitos)")

    @field_validator("meter_serial_c0", "meter_serial_c1")
    @classmethod
    def validate_meter_serial(cls, v: str) -> str:
        s = v.strip()
        if not s.isdigit():
            raise ValueError("O número de série deve conter apenas dígitos numéricos.")
        if len(s) > 11:
            raise ValueError("O número de série não pode exceder 11 dígitos.")
        return s

    @field_validator("meter_serial_c1")
    @classmethod
    def validate_different_serials(cls, v: str, info) -> str:
        c0 = info.data.get("meter_serial_c0")
        if c0 and v.strip() == c0.strip():
            raise ValueError("Os contadores dos canais 0 e 1 devem ser distintos.")
        return v

