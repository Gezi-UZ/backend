from abc import ABC, abstractmethod
import uuid
from typing import List, Optional
from app.modules.users.domain.entities.user import Utilizador
from app.modules.users.domain.entities.schemas import UserCreate, UserUpdate

class IUserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> Optional[Utilizador]:
        pass
        
    @abstractmethod
    def get_by_telefone(self, telefone: str) -> Optional[Utilizador]:
        pass

    @abstractmethod
    def create(self, user: UserCreate) -> Utilizador:
        pass

    @abstractmethod
    def update(self, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[Utilizador]:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Utilizador]:
        pass
