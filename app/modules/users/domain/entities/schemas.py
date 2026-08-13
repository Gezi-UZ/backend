from pydantic import BaseModel
import uuid
from datetime import datetime

class UserBase(BaseModel):
    telefone: str
    nome: str
    papel: str = "cliente"
    biometria_activa: bool = False

class UserCreate(UserBase):
    id: uuid.UUID  # Should come from Supabase Auth

class UserUpdate(BaseModel):
    nome: str | None = None
    biometria_activa: bool | None = None

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
