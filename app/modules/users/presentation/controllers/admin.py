from fastapi import APIRouter, Depends
from typing import List
from app.modules.auth.presentation.dependencies import get_admin_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.users.domain.entities.schemas import UserResponse, AdminCreateUserRequest, AdminUpdateUserStatusRequest
from app.modules.users.presentation.dependencies import get_list_users_usecase, get_create_admin_user_usecase, get_update_user_status_usecase
from app.modules.users.application.usecases.list_users import ListUsersUseCase
from app.modules.users.application.usecases.create_admin_user import CreateAdminUserUseCase
from app.modules.users.application.usecases.update_user_status import UpdateUserStatusUseCase
import uuid

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
    return usecase.execute(skip=skip, limit=limit)

@router.post("/users", response_model=UserResponse)
def create_admin_user(
    data: AdminCreateUserRequest,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: CreateAdminUserUseCase = Depends(get_create_admin_user_usecase)
):
    """
    Create a new admin user.
    """
    return usecase.execute(data)

@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: uuid.UUID,
    data: AdminUpdateUserStatusRequest,
    admin_user: AuthUser = Depends(get_admin_user),
    usecase: UpdateUserStatusUseCase = Depends(get_update_user_status_usecase)
):
    """
    Activate or deactivate a user.
    """
    return usecase.execute(user_id, data.is_active)
