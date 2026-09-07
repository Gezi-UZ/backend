from app.modules.users.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.modules.users.domain.entities.schemas import AdminCreateUserRequest, UserResponse
from fastapi import HTTPException, status

class CreateAdminUserUseCase:
    def __init__(self, user_repo: SQLAlchemyUserRepository):
        self.user_repo = user_repo

    def execute(self, data: AdminCreateUserRequest) -> UserResponse:
        existing_user = self.user_repo.get_by_id(data.id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this ID already exists"
            )
            
        from app.modules.users.domain.entities.schemas import UserCreate
        create_data = UserCreate(
            id=data.id,
            telefone=data.telefone,
            nome=data.nome,
            papel=data.papel
        )
        
        user = self.user_repo.create(create_data)
        return UserResponse.model_validate(user)
