from app.modules.iot.domain.entities.iot import DispositivoIoT
import uuid
from sqlalchemy import String, Boolean, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base, TimestampMixin
from app.modules.users.domain.entities.user import Utilizador

class Contador(Base, TimestampMixin):
    __tablename__ = "contador"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    numero_serie: Mapped[str] = mapped_column(String, unique=True, index=True)
    estado: Mapped[str] = mapped_column(String, default="INACTIVE")
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    kwh_saldo: Mapped[float] = mapped_column(Double, default=0.0)
    ultima_sincronizacao: Mapped[datetime] = mapped_column(nullable=True)
    
    # Chaves Estrangeiras
    utilizador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilizador.id"))
    # O dispositivo_id ser nullable=True permite ter contadores no sistema antes de instalar o hardware
    dispositivo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dispositivo_iot.id"), unique=True, nullable=True)
    
    # Relacionamentos (Lembrar de descomentar em user.py depois)
    utilizador: Mapped["Utilizador"] = relationship(back_populates="contadores")
    dispositivo: Mapped["DispositivoIoT"] = relationship(back_populates="contador")