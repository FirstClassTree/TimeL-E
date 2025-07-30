# db_service/app/notification_service.py

import httpx
from .db_core.models import User
from .db_core.config import settings

import logging

logger = logging.getLogger(__name__)

def send_email_notification(user: User):
    """
    Sends a notification email to the given user.
    """
    subject = f"{settings.APP_NAME} Reminder: It's time to shop again!"
    content = f"""
     Hi {user.name},

     Just a friendly reminder to reorder your favorite products!

     Log in now to see your products and deals waiting for you!

     – Your Grocery Team at {settings.APP_NAME}
     """

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": settings.NOTIFICATION_FROM_EMAIL,
                "to": [user.email_address],
                "subject": subject,
                "text": content
            }
        )
        response.raise_for_status()
        logger.info(f"[EMAIL] Sent to {user.email_address}")

    except httpx.HTTPStatusError as e:
        logger.error(f"[EMAIL ERROR] Failed to send to {user.email_address}; {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Unexpected error: {e}")
