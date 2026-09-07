"""
Modelo de auditoria — regista as acções administrativas críticas do sistema.
"""
import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy.sql import func

from app.core.database import Base


class LogAuditoria(Base):
    """
    Tabela central de auditoria. Regista quem fez o quê, a que entidade e quando.

    Exemplos de acções:
      - CORTE_ENERGIA: Admin X cortou energia no contador Y
      - RELIGACAO_ENERGIA: Admin X religou energia no contador Y
      - CRIAR_ADMIN: Admin X criou o administrador Z
      - DESACTIVAR_UTILIZADOR: Admin X desactivou o utilizador Z
      - EDITAR_CONTADOR: Admin X editou os dados do contador Y
      - COMANDO_OTA: Admin X enviou firmware OTA ao módulo IoT W
    """
    __tablename__ = "log_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="SET NULL"),
        nullable=True,
    )
    accao: Mapped[str] = mapped_column(String(100))      # Ex: "CORTE_ENERGIA"
    entidade: Mapped[str] = mapped_column(String(100))   # Ex: "contador", "utilizador"
    entidade_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # UUID como string
    detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)       # JSON ou descrição livre
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())
