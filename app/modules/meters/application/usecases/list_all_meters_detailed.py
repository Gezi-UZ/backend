from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.schemas import AdminMeterDetailResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.meters.infrastructure.repositories.meter_repository import SQLAlchemyMeterRepository

class ListAllMetersDetailedUseCase:
    def __init__(self, meter_repo: SQLAlchemyMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[AdminMeterDetailResponse]:
        results = self.meter_repo.get_all_with_details(status=status, skip=skip, limit=limit)
        return [AdminMeterDetailResponse.model_validate(r) for r in results]
