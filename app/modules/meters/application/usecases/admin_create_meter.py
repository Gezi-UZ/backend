from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.schemas import AdminMeterCreate
from fastapi import HTTPException
import uuid

class AdminCreateMeterUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, meter_data: AdminMeterCreate) -> Contador:
        existing = self.meter_repo.get_by_serial_number(meter_data.serial_number)
        if existing:
            raise HTTPException(status_code=409, detail="Número de série já registado")
            
        return self.meter_repo.create(meter_data.owner_id, meter_data)
