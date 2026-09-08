from app.modules.meters.infrastructure.repositories.meter_repository import SQLAlchemyMeterRepository
from app.modules.meters.domain.entities.schemas import MeterResponse
import uuid
from fastapi import HTTPException, status
from typing import Optional
from app.modules.audit.application.usecases.create_audit_log import CreateAuditLogUseCase

class RevokeMeterAccessUseCase:
    def __init__(self, meter_repo: SQLAlchemyMeterRepository, audit_usecase: CreateAuditLogUseCase):
        self.meter_repo = meter_repo
        self.audit_usecase = audit_usecase

    def execute(self, meter_id: uuid.UUID, admin_id: Optional[uuid.UUID] = None) -> MeterResponse:
        meter = self.meter_repo.get_by_id(meter_id)
        if not meter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meter not found"
            )
            
        updated_meter = self.meter_repo.revoke_owner(meter_id)
        
        self.audit_usecase.execute(
            accao="REVOGAR_ACESSO_CONTADOR",
            entidade="contador",
            entidade_id=str(meter_id),
            admin_id=admin_id
        )
        
        return MeterResponse.model_validate(updated_meter)
