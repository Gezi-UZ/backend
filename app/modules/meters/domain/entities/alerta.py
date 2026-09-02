import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.domain.entities.user import Utilizador
    from app.modules.meters.domain.entities.meter import Contador

class Alerta(Base, TimestampMixin):
    __tablename__ = 'alerta'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String)
    mensagem: Mapped[str] = mapped_column(String)

    # Chaves Estrangeiras
    utilizador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilizadores.id"))
    contador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contador.id"))

    # Relacionamentos
    utilizador: Mapped["Utilizador"] = relationship()
    contador: Mapped["Contador"] = relationship()
