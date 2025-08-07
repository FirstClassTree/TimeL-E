# db_service/app/scheduler.py

import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import traceback
from .db_core.database import SessionLocal
from .db_core.models import User
from .notification_service import send_email_notification
import logging

logger = logging.getLogger(__name__)

def process_scheduled_user_notifications():
    """Run hourly to flag/schedule user notifications and send emails to users who opted in."""
    now = datetime.datetime.now(datetime.UTC)
    db: Session = SessionLocal()

    try:
        users = db.query(User).all()
        for user in users:
            if not user.order_notifications_next_scheduled_time:
                continue  # skip uninitialized users

            if now >= user.order_notifications_next_scheduled_time:
                user.last_notification_sent_at = now

                # flag as pending
                user.pending_order_notification = True

                # send email if enabled
                if user.order_notifications_via_email:
                    send_email_notification(user)

                # schedule next time

                interval = datetime.timedelta(days=user.days_between_order_notifications or 7)
                # users who are barely late get bumped. users severely late get aligned by multiple intervals ahead.
                # never miss the tick due to rounding or precision issues.
                missed_intervals = max(1, (now - user.order_notifications_next_scheduled_time) // interval + 1)
                user.order_notifications_next_scheduled_time += missed_intervals * interval

                logger.info(f"User {user.id}: scheduled {missed_intervals} missed notification(s), next at {user.order_notifications_next_scheduled_time.isoformat()}")

        db.commit()

    except SQLAlchemyError as db_err:
        db.rollback()
        logger.error("[Scheduler] Database error during notification processing:")
        logger.error(f"  └── {type(db_err).__name__}: {db_err}")
        logger.error(traceback.format_exc())  # full traceback for debugging

    except Exception as e:
        logger.error("[Scheduler] Unexpected error during notification processing:")
        logger.error(f"  └── {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())

    finally:
        db.close()

