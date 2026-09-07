from sqlalchemy.orm import Session
from app.modules.audit.domain.entities.audit import LogAuditoria
import uuid
from typing import List, Optional

class SQLAlchemyAuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        admin_id: Optional[uuid.UUID],
        accao: str,
        entidade: str,
        entidade_id: Optional[str] = None,
        detalhes: Optional[str] = None
    ) -> LogAuditoria:
        log = LogAuditoria(
            admin_id=admin_id,
            accao=accao,
            entidade=entidade,
            entidade_id=entidade_id,
            detalhes=detalhes
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_all(self, skip: int = 0, limit: int = 20) -> tuple[List[LogAuditoria], int]:
        query = self.db.query(LogAuditoria)
        total = query.count()
        logs = query.order_by(LogAuditoria.criado_em.desc()).offset(skip).limit(limit).all()
        return logs, total
