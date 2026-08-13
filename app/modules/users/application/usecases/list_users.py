from app.modules.users.domain.repositories.user_repository import IUserRepository
from app.modules.users.domain.entities.user import Utilizador
from typing import List

class ListUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[Utilizador]:
        return self.user_repo.get_all(skip=skip, limit=limit)
