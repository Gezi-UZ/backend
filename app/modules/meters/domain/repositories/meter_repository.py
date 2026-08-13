from abc import ABC, abstractmethod
import uuid
from typing import List, Optional
from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.schemas import MeterCreate, MeterUpdate

class IMeterRepository(ABC):
    @abstractmethod
    def get_by_id(self, meter_id: uuid.UUID) -> Optional[Contador]:
        pass
        
    @abstractmethod
    def get_by_serial_number(self, serial_number: str) -> Optional[Contador]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: uuid.UUID) -> List[Contador]:
        pass

    @abstractmethod
    def create(self, user_id: uuid.UUID, meter: MeterCreate) -> Contador:
        pass

    @abstractmethod
    def update(self, meter_id: uuid.UUID, meter_update: MeterUpdate) -> Optional[Contador]:
        pass

    @abstractmethod
    def get_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Contador]:
        pass
