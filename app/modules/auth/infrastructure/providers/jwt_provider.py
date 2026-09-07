import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status
from app.core.config import settings
from app.modules.auth.domain.repositories.jwt_provider import IJWTProvider
from app.modules.auth.domain.entities.auth import TokenPayload

class SupabaseJWTProvider(IJWTProvider):
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.jwks_url = settings.supabase_jwks_url
        self.jwks_client = PyJWKClient(self.jwks_url) if self.jwks_url and self.algorithm in ["RS256", "ES256"] else None

    def verify_token(self, token: str) -> TokenPayload:
        if not self.secret_key and not self.jwks_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT Secret Key or JWKS URL not configured",
            )
            
        try:
            if self.algorithm in ["RS256", "ES256"] and self.jwks_client:
                signing_key = self.jwks_client.get_signing_key_from_jwt(token)
                key = signing_key.key
            else:
                key = self.secret_key
                
            payload = jwt.decode(
                token, 
                key, 
                algorithms=[self.algorithm],
                options={"verify_aud": False}
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
