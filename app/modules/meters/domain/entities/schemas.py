from pydantic import BaseModel, Field
import uuid
from typing import Optional
from datetime import datetime

class MeterLocation(BaseModel):
    latitude: float
    longitude: float
    address: str

class MeterCreate(BaseModel):
    serial_number: str
    label: str
    location: MeterLocation

class MeterUpdate(BaseModel):
    label: Optional[str] = None
    location: Optional[MeterLocation] = None

class MeterResponse(BaseModel):
    meter_id: uuid.UUID = Field(alias="id") # The docs use 'meter_id' but DB has 'id'
    serial_number: str
    label: Optional[str]
    location: Optional[MeterLocation]
    status: str = Field(alias="estado")
    credit_kwh: float = Field(alias="kwh_saldo")
    relay_state: bool = Field(alias="estado_rele")
    last_recharge_at: Optional[datetime] = Field(alias="ultima_recarga")

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
        return super().model_validate(obj, *args, **kwargs)

class MeterStatusResponse(BaseModel):
    status: str = Field(alias="estado")
    credit_kwh: float = Field(alias="kwh_saldo")
    relay_state: bool = Field(alias="estado_rele")
    last_seen_at: Optional[datetime] = Field(alias="ultima_sincronizacao")

    class Config:
        from_attributes = True
        populate_by_name = True
