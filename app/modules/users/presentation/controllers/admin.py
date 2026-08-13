from fastapi import APIRouter, Depends
from typing import List
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.users.domain.entities.schemas import UserResponse
from app.modules.users.presentation.dependencies import get_list_users_usecase
from app.modules.users.application.usecases.list_users import ListUsersUseCase

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: ListUsersUseCase = Depends(get_list_users_usecase)
):
    """
    List all users (Admin only).
    """
    return usecase.execute(skip=skip, limit=limit)
