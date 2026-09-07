from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.schemas import MeterCreate
from fastapi import HTTPException
import uuid

from app.modules.meters.domain.entities.schemas import MeterCreate, MeterUpdate

class RegisterMeterUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID, meter_data: MeterCreate) -> Contador:
        existing = self.meter_repo.get_by_serial_number(meter_data.serial_number)
        if not existing:
            raise HTTPException(status_code=404, detail="Contador não encontrado no sistema. Entre em contacto com a administração.")
            
        if existing.utilizador_id is not None and existing.utilizador_id != user_id:
            raise HTTPException(status_code=403, detail="Contador pertence a outro proprietário.")

        # Update the meter with the user's provided label and set them as owner
        update_data = MeterUpdate(
            label=meter_data.label,
            location=meter_data.location,
            owner_id=user_id
        )
        return self.meter_repo.update(existing.id, update_data)
