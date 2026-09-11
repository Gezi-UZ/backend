"""
ProcessAckUseCase — Processa a confirmacao (ACK) do ESP32 via MQTT.

Quando o ESP32 confirma que aplicou um comando (ex: recarga de energia),
este use case atualiza:
  - ComandoIoT.estado → ACK_RECEIVED
  - Recarga.estado → CONCLUIDA
  - Contador.kwh_saldo e ultima_recarga
  - Emite evento SSE para notificar o Flutter
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.meters.domain.entities.meter import Contador

logger = logging.getLogger(__name__)


class ProcessAckUseCase:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, serial: str, payload: dict):
        """
        Processa ACK do ESP32.

        Payload esperado:
        {
            "command_id": "uuid-do-comando",
            "status": "OK",
            "kwh_applied": 20.5,
            "timestamp": "2026-09-03T14:00:00Z"
        }
        """
        command_id = payload.get("command_id")
        if not command_id:
            logger.warning(f"ACK: Payload sem command_id de {serial}")
            return

        # Encontrar o comando na BD
        comando = (
            self.db.query(ComandoIoT)
            .filter(ComandoIoT.id == command_id)
            .first()
        )

        if not comando:
            logger.warning(f"ACK: Comando '{command_id}' nao encontrado")
            return

        # Atualizar estado do comando
        comando.estado = "ACK_RECEIVED"

        # Encontrar o contador pelo serial
        contador = (
            self.db.query(Contador)
            .filter(Contador.numero_serie == serial)
            .first()
        )
        if contador:
            now = datetime.utcnow()
            contador.ultima_sincronizacao = now
            contador.is_online = True
            contador.estado = "ONLINE"
            if contador.dispositivo:
                contador.dispositivo.ultimo_heartbeat = now

        # Se o comando esta ligado a uma recarga, finalizar o ciclo
        if comando.recarga_id:
            recarga = (
                self.db.query(Recarga)
                .filter(Recarga.id == comando.recarga_id)
                .first()
            )

            if recarga:
                recarga.estado = "CONCLUIDA"
                recarga.recarregado_em = datetime.utcnow()

                # Atualizar saldo do contador
                kwh_applied = payload.get("kwh_applied", recarga.kwh_creditado or 0)
                if contador:
                    contador.kwh_saldo = (contador.kwh_saldo or 0) + kwh_applied
                    contador.ultima_recarga = datetime.utcnow()

                logger.info(
                    f"ACK: Recarga '{recarga.id}' concluida. "
                    f"+{kwh_applied} kWh para contador '{serial}'"
                )

                # Emitir evento SSE
                self._emit_sse_event(str(recarga.id), {
                    "event": "status_update",
                    "data": {
                        "recharge_id": str(recarga.id),
                        "status": "CONCLUIDA",
                        "token": recarga.token_sts,
                        "kwh_applied": kwh_applied,
                        "credit_kwh": kwh_applied,
                        "amount_mzn": float(recarga.montante_pago) if recarga.montante_pago else 0.0,
                        "applied_at": datetime.utcnow().isoformat() + "Z",
                    }
                })

        self.db.commit()
        logger.info(f"ACK: Comando '{command_id}' processado para {serial}")

    def _emit_sse_event(self, recharge_id: str, event: dict):
        """Publica evento no EventBus para os subscribers SSE."""
        try:
            from app.core.event_bus import event_bus

            # O event_bus usa asyncio, mas estamos numa thread sync.
            # Usamos asyncio.run_coroutine_threadsafe para publicar.
            try:
                loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(
                    event_bus.publish(recharge_id, event), loop
                )
            except RuntimeError:
                # Nao ha event loop activo nesta thread,
                # criar um temporario
                asyncio.run(event_bus.publish(recharge_id, event))

        except Exception as e:
            logger.error(f"ACK: Erro ao emitir evento SSE: {e}")
