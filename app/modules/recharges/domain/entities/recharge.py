import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.payments.domain.entities.payment import Pagamento
    from app.modules.recharges.domain.entities.recharge_breakdown import DesdobramentoRecarga
    from app.modules.meters.domain.entities.meter import Contador

class Recarga(Base, TimestampMixin):
    __tablename__ = "recarga"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    montante_pago: Mapped[float] = mapped_column(Double)
    moeda: Mapped[str] = mapped_column(String, default="MZN")
    kwh_creditado: Mapped[float] = mapped_column(Double, nullable=True) # So eh preenchido apos calculo
    metodo: Mapped[str] = mapped_column(String, default="M-PESA")
    
    # Estados possiveis: PENDING, PAYMENT_PROCESSING, CONFIRMED, MQTT_SENT, ACK_RECEIVED, FAILED, REFUNDED
    estado: Mapped[str] = mapped_column(String, default="PENDING")

    # Token STS CREDELEC gerado após confirmação de pagamento
    token_sts: Mapped[str] = mapped_column(String, nullable=True, unique=True, index=True)
    token_sts_usado: Mapped[bool] = mapped_column(Boolean, default=False)  # RN10 — uso único

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