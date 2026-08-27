import uuid 
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.meters.domain.entities.meter import Contador
    from app.modules.payments.domain.entities.payment import Pagamento

class Utilizador(Base, TimestampMixin):
    __tablename__ = "utilizadores"

    id: Mapped[uuid.UUID] = mapped_column(
      ForeignKey("auth.users.id", ondelete="CASCADE"),
      primary_key=True
    )
    telefone: Mapped[str] = mapped_column(
      String(9), 
      unique=True,
      index=True,
    )
    nome: Mapped[str] = mapped_column(String)
    papel: Mapped[str] = mapped_column(String, default="cliente")

    biometria_activa: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relacionamentos
    contadores: Mapped[list["Contador"]] = relationship(back_populates="utilizador")
    pagamentos: Mapped[list["Pagamento"]] = relationship(back_populates="utilizador")