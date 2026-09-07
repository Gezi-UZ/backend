from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional, List

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    admin_id: Optional[uuid.UUID]
    accao: str
    entidade: str
    entidade_id: Optional[str]
    detalhes: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
