from app.modules.payments.domain.entities.payment import Pagamento
from app.modules.recharges.domain.entities.recharge_breakdown import DesdobramentoRecarga
from app.modules.meters.domain.entities.meter import Contador
import uuid
from sqlalchemy import String, Boolean, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base, TimestampMixin
# Usaremos TYPE_CHECKING para evitar circular imports se necessário, 
# ou importamos directamente caso a estrutura permita.

class Recarga(Base, TimestampMixin):
    __tablename__ = "recarga"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    montante_pago: Mapped[float] = mapped_column(Double)
    moeda: Mapped[str] = mapped_column(String, default="MZN")
    kwh_creditado: Mapped[float] = mapped_column(Double, nullable=True) # So eh preenchido apos calculo
    metodo: Mapped[str] = mapped_column(String, default="M-PESA")
    
    # Estados possiveis: PENDING, PAID, MQTT_SENT, COMPLETED, FAILED
    estado: Mapped[str] = mapped_column(String, default="PENDING") 
    
    is_primeira_compra_mes: Mapped[bool] = mapped_column(Boolean, default=False)
    recarregado_em: Mapped[datetime] = mapped_column(nullable=True)

    # Chave Estrangeira
    contador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contador.id"))

    # Relacionamentos
    contador: Mapped["Contador"] = relationship(back_populates="recargas")
    
    # Relacao 1 para 1 com Desdobramento
    desdobramento: Mapped["DesdobramentoRecarga"] = relationship(
        back_populates="recarga", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    # Relacao 1 para N com Pagamentos (varias tentativas permitidas)
    pagamentos: Mapped[list["Pagamento"]] = relationship(back_populates="recarga")