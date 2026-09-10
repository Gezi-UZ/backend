"""
Endpoints de Notificações do Utilizador.

GET  /notifications          — Listar notificações (paginado)
PATCH /notifications/{id}/read — Marcar como lida
PATCH /notifications/read-all  — Marcar todas como lidas
GET  /notifications/preferences — Obter preferências
PUT  /notifications/preferences — Actualizar preferências
"""
import uuid
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.auth.domain.entities.auth import AuthUser

logger = logging.getLogger(__name__)

router = APIRouter()

def get_current_user_id(user: AuthUser = Depends(get_current_user)) -> uuid.UUID:
    return user.id


# ── Schemas ──────────────────────────────────────────────────────────────────

class NotificationSchema(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    body: str
    is_read: bool
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationSchema]
    unread_count: int
    total: int


class NotificationPreferencesSchema(BaseModel):
    low_balance_enabled: bool = True
    recharge_confirmed_enabled: bool = True
    payment_failed_enabled: bool = True


# ── Helpers ──────────────────────────────────────────────────────────────────

def _row_to_schema(row) -> NotificationSchema:
    return NotificationSchema(
        id=row.id,
        type=row.type,
        title=row.title,
        body=row.body,
        is_read=row.is_read,
        metadata=row.metadata,
        created_at=row.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=NotificationListResponse)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Lista as notificações do utilizador autenticado."""
    from app.modules.notifications.domain.entities.notification import NotificacaoUtilizador

    query = db.query(NotificacaoUtilizador).filter(
        NotificacaoUtilizador.user_id == user_id
    )
    if unread_only:
        query = query.filter(NotificacaoUtilizador.is_read == False)

    total = query.count()
    unread_count = db.query(NotificacaoUtilizador).filter(
        NotificacaoUtilizador.user_id == user_id,
        NotificacaoUtilizador.is_read == False,
    ).count()

    notifications = (
        query.order_by(NotificacaoUtilizador.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NotificationListResponse(
        notifications=[
            NotificationSchema(
                id=n.id,
                type=n.type,
                title=n.title,
                body=n.body,
                is_read=n.is_read,
                metadata=n.metadata_,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        unread_count=unread_count,
        total=total,
    )


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Marca uma notificação específica como lida."""
    from app.modules.notifications.domain.entities.notification import NotificacaoUtilizador

    notification = db.query(NotificacaoUtilizador).filter(
        NotificacaoUtilizador.id == notification_id,
        NotificacaoUtilizador.user_id == user_id,
    ).first()

    if not notification:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notificação não encontrada.")

    notification.is_read = True
    db.commit()
    return {"success": True}


@router.patch("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Marca todas as notificações do utilizador como lidas."""
    from app.modules.notifications.domain.entities.notification import NotificacaoUtilizador

    db.query(NotificacaoUtilizador).filter(
        NotificacaoUtilizador.user_id == user_id,
        NotificacaoUtilizador.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"success": True}


@router.get("/preferences", response_model=NotificationPreferencesSchema)
def get_preferences(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Obtém as preferências de notificação do utilizador."""
    from app.modules.notifications.domain.entities.notification import PreferenciasNotificacao

    prefs = db.query(PreferenciasNotificacao).filter(
        PreferenciasNotificacao.user_id == user_id
    ).first()

    if not prefs:
        # Retornar defaults se não existir ainda
        return NotificationPreferencesSchema()

    return NotificationPreferencesSchema(
        low_balance_enabled=prefs.low_balance_enabled,
        recharge_confirmed_enabled=prefs.recharge_confirmed_enabled,
        payment_failed_enabled=prefs.payment_failed_enabled,
    )


@router.put("/preferences", response_model=NotificationPreferencesSchema)
def update_preferences(
    body: NotificationPreferencesSchema,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Actualiza as preferências de notificação do utilizador (upsert)."""
    from app.modules.notifications.domain.entities.notification import PreferenciasNotificacao

    prefs = db.query(PreferenciasNotificacao).filter(
        PreferenciasNotificacao.user_id == user_id
    ).first()

    if prefs:
        prefs.low_balance_enabled = body.low_balance_enabled
        prefs.recharge_confirmed_enabled = body.recharge_confirmed_enabled
        prefs.payment_failed_enabled = body.payment_failed_enabled
    else:
        prefs = PreferenciasNotificacao(
            user_id=user_id,
            low_balance_enabled=body.low_balance_enabled,
            recharge_confirmed_enabled=body.recharge_confirmed_enabled,
            payment_failed_enabled=body.payment_failed_enabled,
        )
        db.add(prefs)

    db.commit()
    return body
