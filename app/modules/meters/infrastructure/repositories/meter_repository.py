from sqlalchemy.orm import Session
from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.schemas import MeterCreate, MeterUpdate
import uuid
from typing import List, Optional

class SQLAlchemyMeterRepository(IMeterRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, meter_id: uuid.UUID) -> Optional[Contador]:
        return self.db.query(Contador).filter(Contador.id == meter_id).first()
        
    def get_by_serial_number(self, serial_number: str) -> Optional[Contador]:
        return self.db.query(Contador).filter(Contador.numero_serie == serial_number).first()

    def get_by_user_id(self, user_id: uuid.UUID) -> List[Contador]:
        return self.db.query(Contador).filter(Contador.utilizador_id == user_id).all()

    def create(self, user_id: uuid.UUID, meter: MeterCreate) -> Contador:
        db_meter = Contador(
            numero_serie=meter.serial_number,
            label=meter.label,
            latitude=meter.location.latitude,
            longitude=meter.location.longitude,
            address=meter.location.address,
            utilizador_id=user_id,
            estado="PENDING_ACTIVATION"
        )
        self.db.add(db_meter)
        self.db.commit()
        self.db.refresh(db_meter)
        return db_meter

    def update(self, meter_id: uuid.UUID, meter_update: MeterUpdate) -> Optional[Contador]:
        db_meter = self.get_by_id(meter_id)
        if db_meter:
            if meter_update.label is not None:
                db_meter.label = meter_update.label
            if meter_update.location is not None:
                db_meter.latitude = meter_update.location.latitude
                db_meter.longitude = meter_update.location.longitude
                db_meter.address = meter_update.location.address
            self.db.commit()
            self.db.refresh(db_meter)
        return db_meter

    def get_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Contador]:
        query = self.db.query(Contador)
        if status:
            query = query.filter(Contador.estado == status)
        return query.offset(skip).limit(limit).all()
