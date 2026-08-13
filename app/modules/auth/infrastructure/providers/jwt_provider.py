import jwt
from fastapi import HTTPException, status
from app.core.config import settings
from app.modules.auth.domain.repositories.jwt_provider import IJWTProvider
from app.modules.auth.domain.entities.auth import TokenPayload

class SupabaseJWTProvider(IJWTProvider):
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm

    def verify_token(self, token: str) -> TokenPayload:
        if not self.secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT Secret Key not configured",
            )
            
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="authenticated"
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
