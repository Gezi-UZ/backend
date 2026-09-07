import uuid
from typing import Optional
from app.modules.audit.infrastructure.repositories.audit_repository import SQLAlchemyAuditRepository
from app.modules.audit.domain.entities.schemas import AuditLogListResponse, AuditLogResponse

class ListAuditLogsUseCase:
    def __init__(self, audit_repo: SQLAlchemyAuditRepository):
        self.audit_repo = audit_repo

    def execute(self, page: int = 1, page_size: int = 20) -> AuditLogListResponse:
        skip = (page - 1) * page_size
        logs, total = self.audit_repo.get_all(skip=skip, limit=page_size)
        
        return AuditLogListResponse(
            logs=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size
        )
