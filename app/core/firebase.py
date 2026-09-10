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
            # Load the credentials from the JSON string
            service_account_info = json.loads(settings.firebase_service_account)
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
