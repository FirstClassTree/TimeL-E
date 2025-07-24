# db_service/app/notification_service.py

import httpx
from email.message import EmailMessage
import os
from .db_core.models import User

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "timele.connects@gmail.com")
APP_NAME = os.getenv("APP_NAME", "TimeL-E")

def send_email_notification(user: User):
    """
    Sends a notification email to the given user.
    """
    subject = f"{APP_NAME} Reminder: It's time to shop again!"
    content = f"""
     Hi {user.name},

     Just a friendly reminder to reorder your favorite products!

     Log in now to see your products and deals waiting for you!

     – Your Grocery Team at {APP_NAME}
     """

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": FROM_EMAIL,
                "to": [user.email_address],
                "subject": subject,
                "text": content
            }
        )
        response.raise_for_status()
        print(f"[EMAIL] Sent to {user.email_address}")

    except httpx.HTTPStatusError as e:
        print(f"[EMAIL ERROR] Failed to send to {user.email_address}; {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"[EMAIL ERROR] Unexpected error: {e}")
