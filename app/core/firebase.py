import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

def init_firebase():
    """Initializes the Firebase Admin SDK."""
    if not settings.firebase_service_account:
        logger.warning("FIREBASE_SERVICE_ACCOUNT is not set. Push notifications will not work.")
        return

    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        try:
            raw_val = settings.firebase_service_account.strip()
            # Handle string double-quoting or escaping from environment variables
            if raw_val.startswith('"') and raw_val.endswith('"'):
                try:
                    raw_val = json.loads(raw_val)
                except Exception:
                    raw_val = raw_val[1:-1]

            if isinstance(raw_val, str):
                service_account_info = json.loads(raw_val)
            else:
                service_account_info = raw_val

            if isinstance(service_account_info, dict) and "private_key" in service_account_info:
                pk = service_account_info["private_key"]
                if isinstance(pk, str):
                    service_account_info["private_key"] = pk.replace("\\n", "\n")

            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """Sends a push notification to a specific token using FCM."""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
            data=data or {}
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent FCM message: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending FCM message: {e}")
        return False
