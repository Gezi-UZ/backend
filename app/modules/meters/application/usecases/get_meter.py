from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from fastapi import HTTPException
import uuid

class GetMeterUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID, meter_id: uuid.UUID) -> Contador:
        meter = self.meter_repo.get_by_id(meter_id)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado")
        
        if meter.utilizador_id != user_id:
            raise HTTPException(status_code=403, detail="Contador não pertence ao utilizador autenticado")
            
        return meter
