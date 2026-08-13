from abc import ABC, abstractmethod
from app.modules.auth.domain.entities.auth import TokenPayload

class IJWTProvider(ABC):
    @abstractmethod
    def verify_token(self, token: str) -> TokenPayload:
        pass
