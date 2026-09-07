from pydantic import BaseModel, Field
import uuid
from typing import Optional, List
from datetime import datetime


# ─── Request Schemas ──────────────────────────────────────────────────────────

class RechargeInitiateRequest(BaseModel):
    meter_id: uuid.UUID
    amount_mzn: float = Field(..., gt=0, description="Montante em MZN (deve ser positivo)")
    phone: Optional[str] = Field(
        None,
        description=(
            "Número de telefone Mpesa (9 dígitos, ex: 848512345). "
            "Se omitido, usa o telefone do perfil do utilizador."
        ),
        pattern=r"^8[4-7]\d{7}$",
    )


class ManualCodeRequest(BaseModel):
    meter_id: uuid.UUID
    recharge_code: str = Field(..., min_length=1, description="Código CREDELEC obtido por canal externo")


# ─── Response Schemas ─────────────────────────────────────────────────────────

class RechargeBreakdownResponse(BaseModel):
    """Desdobramento detalhado do montante pago."""
    montante_total: float
    val_energia: float
    iva: float
    divida_paga: float
    tx_radio: float
    tx_lixo: float
    kwh_calculado: float


class RechargeInitiateResponse(BaseModel):
    recharge_id: uuid.UUID
    status: str
    amount_mzn: float
    estimated_kwh: float
    payment_status: str = "INITIATED"  # Estado do STK Push: INITIATED, PROCESSING, FAILED
    breakdown: Optional[RechargeBreakdownResponse] = None


class RechargeStatusResponse(BaseModel):
    recharge_id: uuid.UUID
    status: str
    token: Optional[str] = None
    applied_at: Optional[datetime] = None


class RechargeHistoryItem(BaseModel):
    recharge_id: uuid.UUID
    meter_id: uuid.UUID
    amount_mzn: float
    credit_kwh: Optional[float] = None
    status: str
    created_at: datetime = Field(validation_alias="criado_em")

    class Config:
        from_attributes = True
        populate_by_name = True


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int


class RechargeHistoryResponse(BaseModel):
    recharges: List[RechargeHistoryItem]
    pagination: PaginationMeta


class RechargeDashboardResponse(BaseModel):
    total_spent_mzn: float
    total_kwh_purchased: float
    average_consumption_kwh_day: float
    recharge_count: int


class ManualCodeResponse(BaseModel):
    recharge_id: uuid.UUID
    status: str
    credit_kwh: Optional[float] = None

class AdminTransactionResponse(BaseModel):
    recharge_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    meter_id: uuid.UUID
    meter_serial: Optional[str] = None
    amount_mzn: float
    credit_kwh: Optional[float] = None
    payment_method: str
    status: str
    created_at: datetime = Field(validation_alias="criado_em")
    
    class Config:
        from_attributes = True
        populate_by_name = True

class AdminTransactionListResponse(BaseModel):
    transactions: List[AdminTransactionResponse]
    pagination: PaginationMeta
