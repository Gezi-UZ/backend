"""
NotificationService — Serviço centralizado para criar notificações in-app
e enviar push notifications via FCM para os dispositivos do utilizador.
"""
import uuid
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.notifications.domain.entities.notification import NotificacaoUtilizador

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Cria notificações na tabela user_notifications (Supabase Realtime)
    e opcionalmente envia FCM push para dispositivos registados.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: uuid.UUID,
        type: str,
        title: str,
        body: str,
        metadata: Optional[dict] = None,
        send_push: bool = True,
    ) -> NotificacaoUtilizador:
        """
        Cria uma notificação in-app para o utilizador.

        Args:
            user_id: UUID do utilizador.
            type: Tipo de notificação (recharge_success, recharge_failed, low_balance, system).
            title: Título da notificação.
            body: Corpo da mensagem.
            metadata: Dados adicionais (recharge_id, amount, etc.).
            send_push: Se True, tenta enviar FCM push.

        Returns:
            A notificação criada.
        """
        notification = NotificacaoUtilizador(
            id=uuid.uuid4(),
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            is_read=False,
            metadata_=metadata or {},
        )
        self.db.add(notification)
        self.db.flush()  # Persiste sem commit — o caller faz commit

        logger.info(
            f"NotificationService: Notificação '{type}' criada para utilizador '{user_id}'"
        )

        if send_push:
            self._send_push(user_id=user_id, title=title, body=body, data=metadata)

        return notification

    def notify_recharge_success(
        self,
        user_id: uuid.UUID,
        recharge_id: uuid.UUID,
        amount_mzn: float,
        kwh: float,
        meter_number: str,
    ) -> None:
        """Notifica o utilizador que a recarga foi concluída com sucesso."""
        self.create_notification(
            user_id=user_id,
            type="recharge_success",
            title="Recarga concluída!",
            body=f"A sua recarga de {amount_mzn:.0f} MT ({kwh:.2f} kWh) foi aplicada ao contador {meter_number}.",
            metadata={
                "recharge_id": str(recharge_id),
                "amount_mzn": amount_mzn,
                "kwh": kwh,
                "meter_number": meter_number,
            },
        )

    def notify_recharge_failed(
        self,
        user_id: uuid.UUID,
        recharge_id: uuid.UUID,
        amount_mzn: float,
    ) -> None:
        """Notifica o utilizador que a recarga falhou."""
        self.create_notification(
            user_id=user_id,
            type="recharge_failed",
            title="Falha na recarga",
            body=f"O pagamento de {amount_mzn:.0f} MT não foi confirmado. Nenhum valor foi cobrado.",
            metadata={
                "recharge_id": str(recharge_id),
                "amount_mzn": amount_mzn,
            },
        )

    def notify_manual_code_success(
        self,
        user_id: uuid.UUID,
        recharge_id: uuid.UUID,
        kwh: float,
        meter_number: str,
    ) -> None:
        """Notifica o utilizador que o código STS foi aplicado com sucesso."""
        self.create_notification(
            user_id=user_id,
            type="recharge_success",
            title="Código STS aplicado!",
            body=f"{kwh:.2f} kWh adicionados ao contador {meter_number} via código STS.",
            metadata={
                "recharge_id": str(recharge_id),
                "kwh": kwh,
                "meter_number": meter_number,
                "method": "STS_CODE",
            },
        )
    def notify_low_balance(
        self,
        user_id: uuid.UUID,
        meter_id: uuid.UUID,
        meter_number: str,
        kwh_remaining: float,
    ) -> None:
        """Notifica o utilizador que o saldo do contador está baixo."""
        self.create_notification(
            user_id=user_id,
            type="low_balance",
            title="Saldo baixo",
            body=f"O contador {meter_number} tem apenas {kwh_remaining:.2f} kWh de saldo. Recarregue em breve para evitar o corte de energia.",
            metadata={
                "meter_id": str(meter_id),
                "meter_number": meter_number,
                "kwh_remaining": kwh_remaining,
            },
        )

    def notify_out_of_balance(
        self,
        user_id: uuid.UUID,
        meter_id: uuid.UUID,
        meter_number: str,
    ) -> None:
        """Notifica o utilizador que o saldo do contador esgotou."""
        self.create_notification(
            user_id=user_id,
            type="out_of_balance",
            title="Saldo esgotado",
            body=f"O saldo do contador {meter_number} esgotou. A energia foi ou será cortada em breve.",
            metadata={
                "meter_id": str(meter_id),
                "meter_number": meter_number,
            },
        )

    def _send_push(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> None:
        """Envia FCM push para todos os dispositivos do utilizador."""
        try:
            from app.core.firebase import send_push_notification

            # Buscar tokens FCM do utilizador
            from sqlalchemy import text
            rows = self.db.execute(
                text("SELECT fcm_token FROM user_devices WHERE user_id = :uid"),
                {"uid": str(user_id)},
            ).fetchall()

            string_data = {k: str(v) for k, v in (data or {}).items()}

            for row in rows:
                token = row[0]
                success = send_push_notification(
                    token=token,
                    title=title,
                    body=body,
                    data=string_data,
                )
                if not success:
                    logger.warning(
                        f"NotificationService: FCM falhou para token '{token[:20]}...'"
                    )
        except Exception as e:
            logger.error(f"NotificationService: Erro ao enviar push: {e}")
            # Não propagar — a notificação in-app já foi criada
