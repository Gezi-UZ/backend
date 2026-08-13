from app.modules.users.domain.repositories.user_repository import IUserRepository
from app.modules.users.domain.entities.user import Utilizador
from fastapi import HTTPException
import uuid

class GetUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: uuid.UUID) -> Utilizador:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
