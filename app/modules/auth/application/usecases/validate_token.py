from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.auth.domain.repositories.jwt_provider import IJWTProvider
import uuid

class ValidateTokenUseCase:
    def __init__(self, jwt_provider: IJWTProvider):
        self.jwt_provider = jwt_provider

    def execute(self, token: str) -> AuthUser:
        payload = self.jwt_provider.verify_token(token)
        return AuthUser(
            id=uuid.UUID(payload.sub),
            telefone=payload.phone,
            role=payload.role if payload.role in ["cliente", "admin"] else "cliente"
        )
