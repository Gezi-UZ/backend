from app.modules.users.domain.repositories.user_repository import IUserRepository
from app.modules.users.domain.entities.user import Utilizador
from app.modules.users.domain.entities.schemas import UserUpdate
from fastapi import HTTPException
import uuid

class UpdateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: uuid.UUID, user_data: UserUpdate) -> Utilizador:
        user = self.user_repo.update(user_id, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
