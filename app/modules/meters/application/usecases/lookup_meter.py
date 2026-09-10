from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from fastapi import HTTPException

class LookupMeterUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, serial_number: str) -> Contador:
        meter = self.meter_repo.get_by_serial_number(serial_number)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado")
        return meter
