import uuid
from sqlalchemy import Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.modules.recharges.domain.entities.recharge import Recarga

class DesdobramentoRecarga(Base, TimestampMixin):
    __tablename__ = "desdobramento_recarga"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    montante_total: Mapped[float] = mapped_column(Double)
    val_energia: Mapped[float] = mapped_column(Double)
    iva: Mapped[float] = mapped_column(Double)
    divida_paga: Mapped[float] = mapped_column(Double, default=0.0)
    tx_radio: Mapped[float] = mapped_column(Double)
    tx_lixo: Mapped[float] = mapped_column(Double)
    kwh_calculado: Mapped[float] = mapped_column(Double)

    # Chave estrangeira unica garante a relacao 1:1
    recarga_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recarga.id"), unique=True)
    
    recarga: Mapped["Recarga"] = relationship(back_populates="desdobramento")