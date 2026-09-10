from pydantic import BaseModel, Field
import uuid
from typing import Optional
from datetime import datetime

class MeterLocation(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None

class MeterCreate(BaseModel):
    serial_number: str
    label: str
    location: MeterLocation
    canal: int = 0

class MeterUpdate(BaseModel):
    label: Optional[str] = None
    location: Optional[MeterLocation] = None
    owner_id: Optional[uuid.UUID] = None
    canal: Optional[int] = None
    is_primary: Optional[bool] = None

class AdminMeterCreate(MeterCreate):
    owner_id: Optional[uuid.UUID] = None

class MeterResponse(BaseModel):
    meter_id: uuid.UUID = Field(alias="id") # The docs use 'meter_id' but DB has 'id'
    serial_number: str = Field(validation_alias="numero_serie")
    label: Optional[str]
    location: Optional[MeterLocation]
    status: str = Field(alias="estado")
    credit_kwh: float = Field(alias="kwh_saldo")
    relay_state: bool = Field(alias="estado_rele")
    last_recharge_at: Optional[datetime] = Field(alias="ultima_recarga")
    last_seen_at: Optional[datetime] = Field(alias="ultima_sincronizacao")
    is_online: bool = False
    canal: int = 0
    is_primary: bool = Field(alias="is_primary", default=False)

    class Config:
        from_attributes = True
        populate_by_name = True

    # Custom mapping for location since it's flat in the DB
    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if getattr(obj, "latitude", None) is not None:
            obj.location = MeterLocation(
                latitude=obj.latitude,
                longitude=obj.longitude,
                address=obj.address
            )
        # Compute dynamic is_online based on ultima_sincronizacao (threshold: 5 minutes)
        from datetime import timezone, timedelta
        sync_time = getattr(obj, "ultima_sincronizacao", None)
        if sync_time:
            if sync_time.tzinfo is None:
                sync_time = sync_time.replace(tzinfo=timezone.utc)
            obj.is_online = (datetime.now(timezone.utc) - sync_time) <= timedelta(minutes=5)
        else:
            obj.is_online = False
        return super().model_validate(obj, *args, **kwargs)

class MeterStatusResponse(BaseModel):
    status: str = Field(alias="estado")
    credit_kwh: float = Field(alias="kwh_saldo")
    relay_state: bool = Field(alias="estado_rele")
    last_seen_at: Optional[datetime] = Field(alias="ultima_sincronizacao")
    is_online: bool = Field(alias="is_online", default=False)

    class Config:
        from_attributes = True
        populate_by_name = True

class AdminMeterDetailResponse(MeterResponse):
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    device_mac: Optional[str] = None
    firmware_version: Optional[str] = None
