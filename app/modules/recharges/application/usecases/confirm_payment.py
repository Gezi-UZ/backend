"""
ConfirmPaymentUseCase — Pipeline critico: Pagamento → BD → MQTT → SSE.

Quando um pagamento eh confirmado (callback M-Pesa ou token manual valido):
1. Atualiza Pagamento.estado → SUCCESS
2. Atualiza Recarga.estado → CONFIRMED
3. Calcula desdobramento tarifario
4. Grava ComandoIoT na BD
5. Publica comando MQTT para o ESP32
6. Emite evento SSE para o Flutter
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta
import random

from sqlalchemy.orm import Session

from app.modules.payments.domain.entities.payment import Pagamento
from app.modules.recharges.domain.entities.recharge import Recarga
from app.modules.recharges.domain.entities.recharge_breakdown import DesdobramentoRecarga
from app.modules.meters.domain.entities.meter import Contador
from app.modules.iot.domain.entities.comando_iot import ComandoIoT
from app.modules.recharges.domain.services.tariff_calculator import calcular_desdobramento

logger = logging.getLogger(__name__)


class ConfirmPaymentUseCase:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, referencia_mpesa: str) -> dict:
        """
        Confirma um pagamento e dispara o pipeline completo.

        Args:
            referencia_mpesa: Referencia da transacao M-Pesa.

        Returns:
            Dicionario com o resultado da confirmacao.
        """
        # 1. Encontrar o pagamento pela referencia
        pagamento = (
            self.db.query(Pagamento)
            .filter(Pagamento.referencia_mpesa == referencia_mpesa)
            .first()
        )

        if not pagamento:
            logger.error(f"ConfirmPayment: Pagamento com referencia '{referencia_mpesa}' nao encontrado")
            return {"success": False, "error": "Pagamento nao encontrado"}

        if pagamento.estado == "SUCCESS":
            logger.warning(f"ConfirmPayment: Pagamento '{referencia_mpesa}' ja foi confirmado")
            return {"success": False, "error": "Pagamento ja confirmado"}

        # 2. Atualizar estado do pagamento
        pagamento.estado = "SUCCESS"

        # 3. Encontrar a recarga associada
        recarga = (
            self.db.query(Recarga)
            .filter(Recarga.id == pagamento.recarga_id)
            .first()
        )

        if not recarga:
            self.db.commit()
            return {"success": False, "error": "Recarga associada nao encontrada"}

        # 4. Calcular desdobramento tarifario
        desdobramento = calcular_desdobramento(
            montante_total=recarga.montante_pago,
            is_primeira_compra_mes=recarga.is_primeira_compra_mes,
        )

        recarga.kwh_creditado = desdobramento["kwh_calculado"]
        recarga.estado = "CONFIRMED"
        recarga.pagamento_id = pagamento.id

        # Gravar desdobramento se nao existir
        if not recarga.desdobramento:
            breakdown = DesdobramentoRecarga(
                id=uuid.uuid4(),
                recarga_id=recarga.id,
                montante_total=desdobramento["montante_total"],
                val_energia=desdobramento["val_energia"],
                iva=desdobramento["iva"],
                divida_paga=desdobramento["divida_paga"],
                tx_radio=desdobramento["tx_radio"],
                tx_lixo=desdobramento["tx_lixo"],
                kwh_calculado=desdobramento["kwh_calculado"],
            )
            self.db.add(breakdown)

        # 5. Encontrar o contador e o dispositivo IoT
        contador = (
            self.db.query(Contador)
            .filter(Contador.id == recarga.contador_id)
            .first()
        )

        # Atualizar divida pendente no contador
        if contador:
            nova_divida = desdobramento.get("nova_divida", 0.0)
            divida_paga = desdobramento.get("divida_paga", 0.0)
            contador.divida_pendente += nova_divida - divida_paga
            if contador.divida_pendente < 0:
                contador.divida_pendente = 0.0

        if not contador or not contador.dispositivo_id:
            recarga.estado = "CONFIRMED_NO_DEVICE"
            self.db.commit()
            logger.warning(f"ConfirmPayment: Contador sem dispositivo IoT associado")
            return {
                "success": True,
                "status": "CONFIRMED_NO_DEVICE",
                "message": "Pagamento confirmado mas sem dispositivo para enviar comando",
            }
            
        # Determine if the meter is online
        is_online = False
        if contador.ultima_sincronizacao:
            sync_time = contador.ultima_sincronizacao
            if sync_time.tzinfo is None:
                sync_time = sync_time.replace(tzinfo=timezone.utc)
            is_online = (datetime.now(timezone.utc) - sync_time) <= timedelta(minutes=5)
            
        if not is_online:
            # Fallback: Generate STS token
            raw_digits = "".join([str(random.randint(0, 9)) for _ in range(20)])
            token_sts = f"{raw_digits[0:4]}-{raw_digits[4:8]}-{raw_digits[8:12]}-{raw_digits[12:16]}-{raw_digits[16:20]}"
            recarga.token_sts = token_sts
            logger.info(f"ConfirmPayment: Contador offline. Código STS manual gerado para recarga '{recarga.id}'")

        # 6. Criar ComandoIoT na BD
        comando = ComandoIoT(
            id=uuid.uuid4(),
            tipo="RECHARGE",
            estado="ENVIADO",
            hmac_token=recarga.token_sts or "",
            dispositivo_id=contador.dispositivo_id,
            recarga_id=recarga.id,
        )
        self.db.add(comando)

        # 7. Atualizar recarga para MQTT_SENT
        recarga.estado = "MQTT_SENT"

        self.db.commit()

        # 8. Publicar comando MQTT para o ESP32
        try:
            from app.core.mqtt import publish_command

            publish_command(
                meter_serial=contador.numero_serie,
                command_type="APPLY_CREDITS",
                payload={
                    "command_id": str(comando.id),
                    "token": recarga.token_sts or "",
                    "kwh": desdobramento["kwh_calculado"],
                    "issued_at": datetime.utcnow().isoformat() + "Z",
                },
            )
        except Exception as e:
            logger.error(f"ConfirmPayment: Erro ao publicar MQTT: {e}")
            # Nao fazemos rollback — o comando esta na BD e pode ser reenviado

        # 9. Emitir evento SSE
        self._emit_sse_event(str(recarga.id), {
            "event": "status_update",
            "data": {
                "recharge_id": str(recarga.id),
                "status": "MQTT_SENT",
                "kwh": desdobramento["kwh_calculado"],
                "credit_kwh": desdobramento["kwh_calculado"],
                "amount_mzn": recarga.montante_pago,
                "command_id": str(comando.id),
                "token": recarga.token_sts,
            }
        })

        logger.info(
            f"ConfirmPayment: Pipeline completo para recarga '{recarga.id}'. "
            f"Comando MQTT enviado para '{contador.numero_serie}'"
        )

        return {
            "success": True,
            "status": "MQTT_SENT",
            "recharge_id": str(recarga.id),
            "kwh": desdobramento["kwh_calculado"],
        }

    def _emit_sse_event(self, recharge_id: str, event: dict):
        """Publica evento no EventBus para os subscribers SSE."""
        try:
            from app.core.event_bus import event_bus

            try:
                loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(
                    event_bus.publish(recharge_id, event), loop
                )
            except RuntimeError:
                asyncio.run(event_bus.publish(recharge_id, event))
        except Exception as e:
            logger.error(f"ConfirmPayment: Erro ao emitir evento SSE: {e}")
