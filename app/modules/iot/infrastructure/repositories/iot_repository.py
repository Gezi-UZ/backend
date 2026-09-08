from sqlalchemy.orm import Session
from app.modules.iot.domain.entities.iot import DispositivoIoT
from app.modules.meters.domain.entities.meter import Contador
from typing import List, Optional
import uuid

class SQLAlchemyIoTRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_devices(self, skip: int = 0, limit: int = 100) -> tuple[List[dict], int]:
        query = self.db.query(DispositivoIoT)
        
        total = query.count()
        results = query.offset(skip).limit(limit).all()
        
        formatted = []
        for device in results:
            serials = [c.numero_serie for c in device.contadores if c.numero_serie]
            meter_serial = " | ".join(serials) if serials else None
            
            formatted.append({
                "id": device.id,
                "mac_address": device.mac_address,
                "firmware_version": device.firmware_version,
                "estado": device.estado,
                "ultimo_heartbeat": device.ultimo_heartbeat,
                "meter_id": None,
                "meter_serial": meter_serial
            })
            
        return formatted, total
