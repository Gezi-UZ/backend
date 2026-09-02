import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.sql import func

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.iot.domain.entities.iot import DispositivoIoT
    from app.modules.recharges.domain.entities.recharge import Recarga

class ComandoIoT(Base, TimestampMixin):
    __tablename__ = 'comando_iot'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String)
    estado: Mapped[str] = mapped_column(String)
    hmac_token: Mapped[str] = mapped_column(String)
    enviado_em: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=True)

    # Chaves Estrangeiras
    dispositivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dispositivo_iot.id"))
    recarga_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recarga.id"), nullable=True)

    # Relacionamentos
    dispositivo: Mapped["DispositivoIoT"] = relationship()
    recarga: Mapped["Recarga"] = relationship()
