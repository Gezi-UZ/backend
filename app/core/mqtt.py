import logging
import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id)

if settings.mqtt_username and settings.mqtt_password:
    mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logger.info("Connected to MQTT Broker!")
        # Exemplo de subscrição:
        # client.subscribe("credelec/meter/+/telemetry")
        # client.subscribe("credelec/meter/+/ack")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {reason_code}")

mqtt_client.on_connect = on_connect

def start_mqtt():
    try:
        # Apenas conecta se o broker estiver configurado
        if settings.mqtt_broker:
            logger.info(f"Connecting to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}")
            mqtt_client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
            mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"MQTT Connection Error: {e}")

def stop_mqtt():
    if settings.mqtt_broker:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("Disconnected from MQTT Broker")
