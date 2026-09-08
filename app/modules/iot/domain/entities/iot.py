import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.meters.domain.entities.meter import Contador


class DispositivoIoT(Base, TimestampMixin):
    __tablename__ = 'dispositivo_iot'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    mac_address: Mapped[str] = mapped_column(
      String,
      unique=True,
      index=True
    )
    firmware_version: Mapped[str] = mapped_column(
      String,
      nullable=True
    )
    estado: Mapped[str] = mapped_column(
      String,
      default='FACTORY'
    )
    ultimo_heartbeat: Mapped[datetime] = mapped_column(nullable=True)


    # Relacionamentos
    contadores: Mapped[list['Contador']] = relationship(back_populates='dispositivo')