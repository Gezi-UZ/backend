from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class UserBase(BaseModel):
    telefone: str | None = None
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
    is_active: bool = True
    created_at: datetime = Field(validation_alias="criado_em")
    updated_at: datetime | None = Field(None, validation_alias="actualizado_em")

    class Config:
        from_attributes = True
        populate_by_name = True

class AdminCreateUserRequest(BaseModel):
    id: uuid.UUID
    telefone: str
    nome: str
    papel: str = "admin"

class AdminUpdateUserStatusRequest(BaseModel):
    is_active: bool
