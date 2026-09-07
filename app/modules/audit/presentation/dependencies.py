from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.audit.infrastructure.repositories.audit_repository import SQLAlchemyAuditRepository
from app.modules.audit.application.usecases.list_audit_logs import ListAuditLogsUseCase
import uuid
from typing import Optional

def get_audit_repository(db: Session = Depends(get_db)):
    return SQLAlchemyAuditRepository(db)

def get_list_audit_logs_usecase(repo: SQLAlchemyAuditRepository = Depends(get_audit_repository)):
    return ListAuditLogsUseCase(repo)

def log_admin_action(
    db: Session,
    admin_id: Optional[uuid.UUID],
    accao: str,
    entidade: str,
    entidade_id: Optional[str] = None,
    detalhes: Optional[str] = None
):
    """
    Utility function to log an admin action directly without injecting the repo.
    Can be used across other admin controllers.
    """
    repo = SQLAlchemyAuditRepository(db)
    repo.log_action(admin_id, accao, entidade, entidade_id, detalhes)
