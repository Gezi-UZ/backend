from fastapi import APIRouter, Depends
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser
from app.modules.users.domain.entities.schemas import UserCreate, UserUpdate, UserResponse
from app.modules.users.presentation.dependencies import (
    get_create_user_usecase,
    get_get_user_usecase,
    get_update_user_usecase
)
from app.modules.users.application.usecases.create_user import CreateUserUseCase
from app.modules.users.application.usecases.get_user import GetUserUseCase
from app.modules.users.application.usecases.update_user import UpdateUserUseCase

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    # In a real app, you might want to force the token ID to match the user_data.id
    current_user: AuthUser = Depends(get_current_user),
    usecase: CreateUserUseCase = Depends(get_create_user_usecase)
):
    """
    Called by the frontend after a successful Supabase Phone Registration to complete the user profile.
    """
    return usecase.execute(user_data)

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: AuthUser = Depends(get_current_user),
    usecase: GetUserUseCase = Depends(get_get_user_usecase)
):
    """
    Get the full database profile for the currently logged-in user.
    """
    return usecase.execute(current_user.id)

@router.put("/me", response_model=UserResponse)
def update_me(
    user_data: UserUpdate,
    current_user: AuthUser = Depends(get_current_user),
    usecase: UpdateUserUseCase = Depends(get_update_user_usecase)
):
    """
    Update the logged-in user's profile.
    """
    return usecase.execute(current_user.id, user_data)
