from app.modules.users.domain.repositories.user_repository import IUserRepository
from app.modules.users.domain.entities.user import Utilizador
from app.modules.users.domain.entities.schemas import UserCreate
from fastapi import HTTPException

class CreateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, user_data: UserCreate) -> Utilizador:
        existing_user = self.user_repo.get_by_id(user_data.id)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already registered")
            
        existing_phone = self.user_repo.get_by_telefone(user_data.telefone)
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already in use")

        return self.user_repo.create(user_data)
