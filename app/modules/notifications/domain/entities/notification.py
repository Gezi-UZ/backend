import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class NotificacaoUtilizador(Base):
    """Notificação in-app para o utilizador (bell icon + AlertsPage)."""
    __tablename__ = "user_notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Tipos: recharge_success, recharge_failed, recharge_status, low_balance, system
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default="NOW()",
    )


class PreferenciasNotificacao(Base):
    """Preferências de notificação por utilizador (toggles da AlertsPage)."""
    __tablename__ = "user_notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    low_balance_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    recharge_confirmed_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_failed_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default="NOW()",
        onupdate=datetime.utcnow,
    )
