from datetime import datetime
from app.modules.users.domain.entities.user import Utilizador
from app.modules.recharges.domain.entities.recharge import Recarga
import uuid
from sqlalchemy import String, Double, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

class Pagamento(Base, TimestampMixin):
    __tablename__ = "pagamento"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    referencia_mpesa: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    montante: Mapped[float] = mapped_column(Double)

    # Estados: INITIATED, SUCCESS, FAILED
    estado: Mapped[str] = mapped_column(String, default="INITIATED")
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())
    recarga_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recarga.id"))
    utilizador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilizadores.id"))
    
    recarga: Mapped["Recarga"] = relationship(back_populates="pagamentos")
    utilizador: Mapped["Utilizador"] = relationship(back_populates="pagamentos")