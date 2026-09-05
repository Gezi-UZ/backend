"""
Modulo MQTT — Comunicacao bidirecional com dispositivos ESP32 via HiveMQ Cloud.

Topicos:
  - credelec/meter/{serial}/cmd         → Backend publica comandos para o ESP32
  - credelec/meter/{serial}/telemetry   → ESP32 publica dados de telemetria
  - credelec/meter/{serial}/ack         → ESP32 confirma que aplicou um comando
"""
import json
import ssl
import logging
import threading
from typing import Any

import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=settings.mqtt_client_id,
    transport=settings.mqtt_transport
)

if settings.mqtt_transport == "websockets":
    mqtt_client.ws_set_options(path="/mqtt")


# Credenciais
if settings.mqtt_username and settings.mqtt_password:
    mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

# TLS (obrigatorio para HiveMQ Cloud na porta 8883)
if settings.mqtt_use_tls:
    mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
    logger.info("MQTT: TLS activado")


# ─── Callbacks ────────────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logger.info("MQTT: Conectado ao Broker com sucesso!")
        # Subscrever aos topicos de telemetria e ack de todos os contadores
        client.subscribe("credelec/meter/+/telemetry", qos=1)
        client.subscribe("credelec/meter/+/ack", qos=1)
        logger.info("MQTT: Subscrito a credelec/meter/+/telemetry e credelec/meter/+/ack")
    else:
        logger.error(f"MQTT: Falha ao conectar ao broker, reason_code={reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    logger.warning(f"MQTT: Desconectado do broker (reason_code={reason_code}). Reconnect automatico activo.")


def on_message(client, userdata, msg):
    """
    Router de mensagens MQTT recebidas.
    Despacha para o handler correcto com base no topico.
    """
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"MQTT: Payload invalido no topico '{topic}': {e}")
        return

    # Extrair o serial do topico: credelec/meter/{serial}/telemetry
    parts = topic.split("/")
    if len(parts) != 4 or parts[0] != "credelec" or parts[1] != "meter":
        logger.warning(f"MQTT: Topico desconhecido: {topic}")
        return

    serial = parts[2]
    msg_type = parts[3]

    if msg_type == "telemetry":
        _handle_telemetry(serial, payload)
    elif msg_type == "ack":
        _handle_ack(serial, payload)
    else:
        logger.warning(f"MQTT: Tipo de mensagem desconhecido: {msg_type}")


# ─── Handlers (executados em background thread) ──────────────────────────────

def _handle_telemetry(serial: str, payload: dict):
    """
    Processa dados de telemetria do ESP32.
    Executado numa thread separada para nao bloquear o loop MQTT.
    """
    def _process():
        try:
            from app.core.database import SessionLocal
            from app.modules.iot.application.usecases.process_telemetry import ProcessTelemetryUseCase

            db = SessionLocal()
            try:
                usecase = ProcessTelemetryUseCase(db)
                usecase.execute(serial, payload)
                logger.info(f"MQTT: Telemetria processada para {serial}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"MQTT: Erro ao processar telemetria de {serial}: {e}")

    thread = threading.Thread(target=_process, daemon=True)
    thread.start()


def _handle_ack(serial: str, payload: dict):
    """
    Processa confirmacao (ACK) do ESP32 de que um comando foi aplicado.
    Executado numa thread separada.
    """
    def _process():
        try:
            from app.core.database import SessionLocal
            from app.modules.iot.application.usecases.process_ack import ProcessAckUseCase

            db = SessionLocal()
            try:
                usecase = ProcessAckUseCase(db)
                usecase.execute(serial, payload)
                logger.info(f"MQTT: ACK processado para {serial}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"MQTT: Erro ao processar ACK de {serial}: {e}")

    thread = threading.Thread(target=_process, daemon=True)
    thread.start()


# Registar callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message


# ─── Funcoes Publicas ─────────────────────────────────────────────────────────

def publish_command(meter_serial: str, command_type: str, payload: dict[str, Any]):
    """
    Publica um comando MQTT para o ESP32 de um contador especifico.

    Topico: credelec/meter/{meter_serial}/cmd
    Payload: JSON com tipo de comando e dados.

    Args:
        meter_serial: Numero de serie do contador (ex: GEZI-00123)
        command_type: Tipo de comando (ex: APPLY_CREDITS, CUT_SUPPLY, RESTORE_SUPPLY)
        payload: Dados adicionais do comando (ex: token STS, kwh)
    """
    topic = f"credelec/meter/{meter_serial}/cmd"
    message = json.dumps({
        "command": command_type,
        **payload,
    })

    result = mqtt_client.publish(topic, message, qos=1)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        logger.info(f"MQTT: Comando '{command_type}' publicado para {meter_serial}")
    else:
        logger.error(f"MQTT: Falha ao publicar comando para {meter_serial} (rc={result.rc})")

    return result


def start_mqtt():
    """Inicia a conexao MQTT ao broker."""
    try:
        if settings.mqtt_broker:
            logger.info(f"MQTT: Conectando a {settings.mqtt_broker}:{settings.mqtt_port} (TLS={settings.mqtt_use_tls})")
            mqtt_client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
            mqtt_client.loop_start()
        else:
            logger.warning("MQTT: Broker nao configurado, pulando conexao")
    except Exception as e:
        logger.error(f"MQTT: Erro de conexao: {e}")


def stop_mqtt():
    """Desliga a conexao MQTT."""
    if settings.mqtt_broker:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("MQTT: Desconectado do Broker")
