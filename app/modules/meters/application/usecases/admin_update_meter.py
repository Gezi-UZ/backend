from app.modules.meters.infrastructure.repositories.meter_repository import SQLAlchemyMeterRepository
from app.modules.meters.domain.entities.schemas import MeterUpdate, MeterResponse
import uuid
from typing import Optional
from fastapi import HTTPException, status

class AdminUpdateMeterUseCase:
    def __init__(self, meter_repo: SQLAlchemyMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, meter_id: uuid.UUID, update_data: MeterUpdate) -> MeterResponse:
        meter = self.meter_repo.get_by_id(meter_id)
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found"
            )
            
        updated_meter = self.meter_repo.update(meter_id, update_data)
        return MeterResponse.model_validate(updated_meter)
