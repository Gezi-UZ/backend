from app.modules.meters.domain.repositories.meter_repository import IMeterRepository
from app.modules.meters.domain.entities.meter import Contador
import uuid
from typing import List

class ListMyMetersUseCase:
    def __init__(self, meter_repo: IMeterRepository):
        self.meter_repo = meter_repo

    def execute(self, user_id: uuid.UUID) -> List[Contador]:
        return self.meter_repo.get_by_user_id(user_id)
