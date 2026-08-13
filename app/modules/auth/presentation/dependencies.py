from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.modules.auth.infrastructure.providers.jwt_provider import SupabaseJWTProvider
from app.modules.auth.application.usecases.validate_token import ValidateTokenUseCase
from app.modules.auth.domain.entities.auth import AuthUser

security = HTTPBearer()

def get_jwt_provider():
    return SupabaseJWTProvider()

def get_validate_token_usecase(
    provider: SupabaseJWTProvider = Depends(get_jwt_provider)
):
    return ValidateTokenUseCase(jwt_provider=provider)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    usecase: ValidateTokenUseCase = Depends(get_validate_token_usecase)
) -> AuthUser:
    token = credentials.credentials
    return usecase.execute(token)

from fastapi import HTTPException, status

def get_admin_user(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires admin privileges",
        )
    return current_user
