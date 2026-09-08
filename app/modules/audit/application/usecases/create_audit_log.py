import uuid
from typing import Optional
from app.modules.audit.infrastructure.repositories.audit_repository import SQLAlchemyAuditRepository
from app.modules.audit.domain.entities.audit import LogAuditoria

class CreateAuditLogUseCase:
    def __init__(self, audit_repo: SQLAlchemyAuditRepository):
        self.audit_repo = audit_repo

    def execute(
        self,
        accao: str,
        entidade: str,
        entidade_id: Optional[str] = None,
        admin_id: Optional[uuid.UUID] = None,
        detalhes: Optional[str] = None
    ) -> LogAuditoria:
        return self.audit_repo.log_action(
            admin_id=admin_id,
            accao=accao,
            entidade=entidade,
            entidade_id=entidade_id,
            detalhes=detalhes
        )
