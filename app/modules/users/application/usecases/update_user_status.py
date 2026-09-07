from app.modules.users.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.modules.users.domain.entities.schemas import UserResponse
import uuid
from fastapi import HTTPException, status

class UpdateUserStatusUseCase:
    def __init__(self, user_repo: SQLAlchemyUserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: uuid.UUID, is_active: bool) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        updated_user = self.user_repo.update_status(user_id, is_active)
        return UserResponse.model_validate(updated_user)
