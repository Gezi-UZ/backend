from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.schemas import MeterCreate
from fastapi import HTTPException
import uuid

class RegisterMeterUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID, meter_data: MeterCreate) -> Contador:
        existing = self.meter_repo.get_by_serial_number(meter_data.serial_number)
        if existing:
            raise HTTPException(status_code=409, detail="Número de série já registado")
            
        # Optional: Here you could call an EDM mock service to check if the serial exists in their system
        # If not, throw 404 "Número de série não reconhecido pelo sistema EDM"

        return self.meter_repo.create(user_id, meter_data)
