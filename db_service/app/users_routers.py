# app/users_routers.py

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session
from sqlalchemy import func
from .db_core.database import SessionLocal
from .db_core.models import User
from pydantic import BaseModel, EmailStr, Field, conint
from typing import Optional
# Removed UUID imports since we're using integer user_ids
# import hashlib
import bcrypt
from datetime import datetime, timedelta, UTC

router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def to_utc(dt: datetime) -> datetime:
    """
    Ensures the given datetime is timezone-aware in UTC.

    - If `dt` is naive (no tzinfo), it's assumed to be in UTC and marked accordingly.
    - If `dt` is timezone-aware, it's converted to UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=UTC)  # assume naive datetime is UTC
    return dt.astimezone(UTC)

class UpdateNotificationSettingsRequest(BaseModel):
    days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
    order_notifications_start_date_time: Optional[datetime] = None
    order_notifications_via_email: Optional[bool] = None

def apply_notification_settings(user: User, payload: UpdateNotificationSettingsRequest) -> bool:
    """Apply notification-related settings to a user. Returns True if updated."""

    updated = False
    now = datetime.now(UTC)

    # Capture current values to calculate next time
    converted_start = to_utc(payload.order_notifications_start_date_time) if payload.order_notifications_start_date_time else None
    stored_start = to_utc(
        user.order_notifications_start_date_time) if user.order_notifications_start_date_time else None
    start_time = converted_start or stored_start or datetime.now(UTC)
    interval_days = payload.days_between_order_notifications or user.days_between_order_notifications or 7
    interval = timedelta(days=interval_days)

    # Update interval
    if payload.days_between_order_notifications is not None:
        user.days_between_order_notifications = payload.days_between_order_notifications
        updated = True

    # Update start time
    if payload.order_notifications_start_date_time is not None:
        user.order_notifications_start_date_time = converted_start
        updated = True

    # Update next scheduled time if either start or interval changed
    if payload.days_between_order_notifications is not None or payload.order_notifications_start_date_time is not None:
        if start_time is None:
            start_time = now
        if now < start_time:
            user.order_notifications_next_scheduled_time = start_time
        else:  # db stored start_time can be in the past
            missed_intervals = max(1, (now - start_time) // interval + 1)
            user.order_notifications_next_scheduled_time = start_time + missed_intervals * interval

    # Update email preference
    if payload.order_notifications_via_email is not None:
        user.order_notifications_via_email = payload.order_notifications_via_email
        updated = True

    return updated

def hash_password(password: str) -> str:
    # return hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def authenticate_user(email: EmailStr, password: str, session: Session):
    user = session.query(User).filter_by(email_address=email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

class CreateUserRequest(BaseModel):
    name: str
    email_address: EmailStr
    password: str
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Notification-related fields that user is allowed to configure
    days_between_order_notifications: Optional[int] = 7
    order_notifications_via_email: Optional[bool] = False
    order_notifications_start_date_time: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user_request: CreateUserRequest, session: Session = Depends(get_db)):
    try:
        # Check for duplicate email or name
        if session.query(User).filter_by(email_address=user_request.email_address).first():
            raise HTTPException(status_code=409, detail="Email address already exists")
        # if session.query(User).filter_by(name=user_request.name).first():
        #     raise HTTPException(status_code=409, detail="Username already exists")

        hashed_pw = hash_password(user_request.password)
        # Get next available user_id (auto-increment would be better but this works)
        max_id = session.query(func.max(User.user_id)).scalar() or 0
        next_id = max_id + 1

        start_time = to_utc(user_request.order_notifications_start_date_time)
        interval_days = user_request.days_between_order_notifications or 7
        
        user = User(
            user_id=next_id,
            name=user_request.name,
            email_address=user_request.email_address,
            hashed_password=hashed_pw,
            phone_number=user_request.phone_number,
            street_address=user_request.street_address,
            city=user_request.city,
            postal_code=user_request.postal_code,
            country=user_request.country,
            days_between_order_notifications=interval_days,
            order_notifications_start_date_time=start_time,
            order_notifications_next_scheduled_time=start_time + timedelta(days=interval_days),
            order_notifications_via_email=user_request.order_notifications_via_email,
            pending_order_notification=False,
            last_notification_sent_at=None,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email_address": user.email_address,
            "phone_number": user.phone_number,
            "street_address": user.street_address,
            "city": user.city,
            "postal_code": user.postal_code,
            "country": user.country,
            "days_between_order_notifications": user.days_between_order_notifications,
            "order_notifications_start_date_time": user.order_notifications_start_date_time,
            "order_notifications_next_scheduled_time": user.order_notifications_next_scheduled_time,
            "pending_order_notification": user.pending_order_notification,
            "order_notifications_via_email": user.order_notifications_via_email,
            "last_notification_sent_at": user.last_notification_sent_at
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user")


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/{user_id}/password", status_code=status.HTTP_200_OK)
def update_user_password(
        user_id: int,
        payload: UpdatePasswordRequest,
        session: Session = Depends(get_db)
):
    try:
        # Fetch user
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash and set new password
        new_hashed = hash_password(payload.new_password)
        user.hashed_password = new_hashed
        session.commit()
        return {"message": "Password updated successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating password: {e}")
        raise HTTPException(status_code=500, detail="Error updating password")

class UpdateEmailRequest(BaseModel):
    current_password: str
    new_email_address: EmailStr

@router.post("/{user_id}/email", status_code=status.HTTP_200_OK)
def update_user_email(
        user_id: int,
        payload: UpdateEmailRequest,
        session: Session = Depends(get_db)
):
    try:
        # Fetch user
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Check for duplicate email (must not already exist)
        existing = session.query(User).filter(
            User.email_address == payload.new_email_address,
            User.user_id != user_id  # Exclude current user
        ).first()
        if existing:
            print("Email address already in use by another user.")
            raise HTTPException(status_code=409, detail="Invalid update request.")

        # Update email
        user.email_address = payload.new_email_address
        session.commit()
        session.refresh(user)
        return {"message": "Email address updated successfully",
                "email_address": user.email_address}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating email: {e}")
        raise HTTPException(status_code=500, detail="Error updating email address")

@router.get("/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_db)):
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email_address": user.email_address,
            "phone_number": user.phone_number,
            "street_address": user.street_address,
            "city": user.city,
            "postal_code": user.postal_code,
            "country": user.country,
            "days_between_order_notifications": user.days_between_order_notifications,
            "order_notifications_start_date_time": user.order_notifications_start_date_time,
            "order_notifications_next_scheduled_time": user.order_notifications_next_scheduled_time,
            "pending_order_notification": user.pending_order_notification,
            "order_notifications_via_email": user.order_notifications_via_email,
            "last_notification_sent_at": user.last_notification_sent_at
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching user")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
    order_notifications_start_date_time: Optional[datetime] = None
    order_notifications_via_email: Optional[bool] = None

# Only non-credential fields can be updated here.
# Attempting to update email/password will have no effect.
@router.patch("/{user_id}")
def update_user(user_id: int, payload: UpdateUserRequest, session: Session = Depends(get_db)):
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        updated = False
        update_data = payload.model_dump(exclude_unset=True)

        # Update allowed fields
        for field, value in update_data.items():
            if field in {"days_between_order_notifications", "order_notifications_start_date_time", "order_notifications_via_email"}:
                continue  # Skip notification fields, delegate to apply_notification_settings()
            setattr(user, field, value)
            updated = True
        # Delegate notification updates to shared logic
        if any(f in update_data for f in {
            "days_between_order_notifications",
            "order_notifications_start_date_time",
            "order_notifications_via_email"
        }):
            notification_updated = apply_notification_settings(user, payload)
            updated = updated or notification_updated

        if updated:
            session.commit()
            session.refresh(user)
            return {"message": "User updated successfully",
                    "user_id": user.user_id,
                    "name": user.name,
                    "email_address": user.email_address,
                    "phone_number": user.phone_number,
                    "street_address": user.street_address,
                    "city": user.city,
                    "postal_code": user.postal_code,
                    "country": user.country,
                    "days_between_order_notifications": user.days_between_order_notifications,
                    "order_notifications_start_date_time": user.order_notifications_start_date_time,
                    "order_notifications_next_scheduled_time": user.order_notifications_next_scheduled_time,
                    "pending_order_notification": user.pending_order_notification,
                    "order_notifications_via_email": user.order_notifications_via_email,
                    "last_notification_sent_at": user.last_notification_sent_at
                    }
        else:
            return {"message": "No changes made"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user")


class DeleteUserRequest(BaseModel):
    password: str


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, payload: DeleteUserRequest, session: Session = Depends(get_db)):
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=403, detail="Password incorrect")
        session.delete(user)
        session.commit()
        return {"message": "User deleted successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting user")

class NotificationSettingsResponse(BaseModel):
    days_between_order_notifications: int
    order_notifications_start_date_time: Optional[datetime]
    order_notifications_next_scheduled_time: Optional[datetime]
    order_notifications_via_email: bool
    pending_order_notification: bool

@router.get("/{user_id}/notification-settings", response_model=NotificationSettingsResponse)
def get_notification_settings(user_id: int, session: Session = Depends(get_db)):
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user_id": user.user_id,
            "days_between_order_notifications": user.days_between_order_notifications,
            "order_notifications_start_date_time": user.order_notifications_start_date_time,
            "order_notifications_next_scheduled_time": user.order_notifications_next_scheduled_time,
            "order_notifications_via_email": user.order_notifications_via_email,
            "pending_order_notification": user.pending_order_notification,
            "last_notification_sent_at": user.last_notification_sent_at
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to update notification settings: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

# class UpdateNotificationSettingsRequest(BaseModel):
#     days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
#     order_notifications_start_date_time: Optional[datetime] = None
#     order_notifications_via_email: Optional[bool] = None

@router.patch("/{user_id}/notification-settings")
def update_notification_settings(user_id: int, payload: UpdateNotificationSettingsRequest,
                                 session: Session = Depends(get_db)):
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        updated = apply_notification_settings(user, payload)

        if updated:
            session.commit()
            session.refresh(user)  # Ensure getting fresh DB values
            return {
                "message": "Notification settings updated successfully",
                "user_id": user.user_id,
                "days_between_order_notifications": user.days_between_order_notifications,
                "order_notifications_start_date_time": user.order_notifications_start_date_time,
                "order_notifications_next_scheduled_time": user.order_notifications_next_scheduled_time,
                "order_notifications_via_email": user.order_notifications_via_email,
                "pending_order_notification": user.pending_order_notification,
                "last_notification_sent_at": user.last_notification_sent_at,
            }
        else:
            return {"message": "No changes made"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to update notification settings: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

class LoginRequest(BaseModel):
    email_address: EmailStr
    password: str

@router.post("/login")
def login_user(payload: LoginRequest, session: Session = Depends(get_db)):
    try:
        user = authenticate_user(payload.email_address, payload.password, session)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email_address": user.email_address,
            "phone_number": user.phone_number,
            "street_address": user.street_address,
            "city": user.city,
            "postal_code": user.postal_code,
            "country": user.country,
            "days_between_order_notifications": user.days_between_order_notifications,
            "order_notifications_start_date_time": user.order_notifications_start_date_time,
            "order_notifications_next_scheduled_time": user.order_notifications_next_scheduled_time,
            "pending_order_notification": user.pending_order_notification,
            "order_notifications_via_email": user.order_notifications_via_email,
            "last_notification_sent_at": user.last_notification_sent_at
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to login user: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
