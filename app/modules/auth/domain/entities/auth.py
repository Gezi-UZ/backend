from pydantic import BaseModel
from typing import Literal
import uuid

class AuthUser(BaseModel):
    id: uuid.UUID
    telefone: str | None = None
    role: Literal["cliente", "admin"] = "cliente"

class TokenPayload(BaseModel):
    sub: str
    phone: str | None = None
    role: Literal["cliente", "admin"] | None = None
    exp: int
