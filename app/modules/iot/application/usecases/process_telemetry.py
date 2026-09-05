"""
ProcessTelemetryUseCase — Processa dados de telemetria recebidos do ESP32 via MQTT.

Atualiza a tabela `contador` com os dados mais recentes do dispositivo
(kWh, estado do rele, heartbeat). Se o saldo estiver abaixo do limiar,
cria um alerta na base de dados.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.meters.domain.entities.meter import Contador
from app.modules.meters.domain.entities.alerta import Alerta

logger = logging.getLogger(__name__)

# Limiar de saldo baixo (kWh) — abaixo disto, gera alerta
LIMIAR_SALDO_BAIXO_KWH = 5.0


class ProcessTelemetryUseCase:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, serial: str, payload: dict):
        """
        Processa telemetria do ESP32.

        Payload esperado do ESP32:
        {
            "kwh": 40.2,
            "relay": true,
            "voltage": 220.5,       // opcional
            "current": 2.1,         // opcional
            "firmware": "1.2.0"     // opcional
        }
        """
        contador = (
            self.db.query(Contador)
            .filter(Contador.numero_serie == serial)
            .first()
        )

        if not contador:
            logger.warning(f"Telemetria: Contador com serie '{serial}' nao encontrado")
            return

        # Atualizar campos do contador
        if "kwh" in payload:
            contador.kwh_saldo = payload["kwh"]
        if "relay" in payload:
            contador.estado_rele = payload["relay"]

        contador.ultima_sincronizacao = datetime.utcnow()
        contador.is_online = True
        contador.estado = "ONLINE"

        # Atualizar firmware do dispositivo IoT se disponivel
        if "firmware" in payload and contador.dispositivo:
            contador.dispositivo.firmware_version = payload["firmware"]
            contador.dispositivo.ultimo_heartbeat = datetime.utcnow()

        # Verificar se saldo esta abaixo do limiar
        if contador.kwh_saldo is not None and contador.kwh_saldo < LIMIAR_SALDO_BAIXO_KWH:
            self._criar_alerta_saldo_baixo(contador)

        self.db.commit()
        logger.info(f"Telemetria: Contador '{serial}' atualizado (kWh={contador.kwh_saldo}, rele={contador.estado_rele})")

    def _criar_alerta_saldo_baixo(self, contador: Contador):
        """Cria um alerta de saldo baixo se nao existir um recente (ultimas 24h)."""
        from datetime import timedelta

        # Verificar se ja existe um alerta recente para evitar spam
        alerta_recente = (
            self.db.query(Alerta)
            .filter(
                Alerta.contador_id == contador.id,
                Alerta.tipo == "SALDO_BAIXO",
                Alerta.criado_em >= datetime.utcnow() - timedelta(hours=24),
            )
            .first()
        )

        if alerta_recente:
            return  # Ja existe alerta recente

        alerta = Alerta(
            id=uuid.uuid4(),
            tipo="SALDO_BAIXO",
            mensagem=f"Saldo baixo no contador {contador.numero_serie}: {contador.kwh_saldo:.1f} kWh restantes",
            utilizador_id=contador.utilizador_id,
            contador_id=contador.id,
        )
        self.db.add(alerta)
        logger.info(f"Telemetria: Alerta SALDO_BAIXO criado para contador '{contador.numero_serie}'")
