from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from fastapi import HTTPException
import uuid

class GetMeterStatusUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, meter_id: uuid.UUID) -> Contador:
        # Same logic as GetMeter, but this specifically returns the entity for the status response mapping
        meter = self.meter_repo.get_by_id(meter_id)
        if not meter:
            raise HTTPException(status_code=404, detail="Contador não encontrado")
        
        from datetime import datetime, timezone, timedelta
        
        # Calculate dynamic online status
        if meter.ultima_sincronizacao:
            # Check if ultima_sincronizacao is naive, if so, assume UTC
            sync_time = meter.ultima_sincronizacao
            if sync_time.tzinfo is None:
                sync_time = sync_time.replace(tzinfo=timezone.utc)
            
            is_recent = (datetime.now(timezone.utc) - sync_time) <= timedelta(minutes=5)
            meter.is_online = is_recent
        else:
            meter.is_online = False
            
        return meter
