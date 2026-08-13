from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
from typing import List, Optional

class ListAllMetersUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Contador]:
        return self.meter_repo.get_all(status=status, skip=skip, limit=limit)
