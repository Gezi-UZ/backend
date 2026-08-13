from app.modules.meters.domain.entities.meter import Contador
import uuid 
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

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

    
    