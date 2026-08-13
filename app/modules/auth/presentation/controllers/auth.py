from fastapi import APIRouter, Depends
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser

router = APIRouter()

@router.get("/me", response_model=AuthUser)
def get_me(current_user: AuthUser = Depends(get_current_user)):
    """
    Returns the authenticated user's profile data extracted from the JWT.
    Used by mobile and web clients to verify session.
    """
    return current_user
