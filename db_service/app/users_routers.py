# app/users_routers.py

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session, aliased
from sqlalchemy import func, and_
from .db_core.database import SessionLocal
from .db_core.models import User, Order, OrderStatusHistory, Cart
from pydantic import BaseModel, EmailStr, Field, conint, ConfigDict
from typing import Optional, Generic, TypeVar, List
# Removed UUID imports since we're using integer user_ids
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
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

# Initialize Argon2id hasher with secure defaults
ph = PasswordHasher(
    memory_cost=65536,  # 64 MB
    time_cost=3,        # 3 iterations
    parallelism=4,      # 4 threads
    hash_len=32,        # 32 byte hash
    salt_len=16         # 16 byte salt
)

def hash_password(password: str) -> str:
    """Hash password using Argon2id"""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def authenticate_user(email: EmailStr, password: str, session: Session):
    user = session.query(User).filter_by(email_address=email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

# Generic response model
T = TypeVar('T')

class ServiceResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] = []
    error: Optional[str] = None
    message: Optional[str] = None

class UserData(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email_address: str
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
    order_notifications_start_date_time: Optional[datetime] = None
    order_notifications_next_scheduled_time: Optional[datetime] = None
    pending_order_notification: Optional[bool] = None
    order_notifications_via_email: Optional[bool] = None
    last_notification_sent_at: Optional[datetime] = None
    last_notifications_viewed_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    has_active_cart: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)

class PasswordUpdateResponse(BaseModel):
    user_id: int
    password_updated: bool

class EmailUpdateResponse(BaseModel):
    user_id: int
    email_address: str

class DeleteResponse(BaseModel):
    user_id: int
    deleted: bool

class NotificationSettingsData(BaseModel):
    user_id: int
    days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
    order_notifications_start_date_time: Optional[datetime] = None
    order_notifications_next_scheduled_time: Optional[datetime] = None
    order_notifications_via_email: Optional[bool] = None
    pending_order_notification: Optional[bool] = None
    last_notification_sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CreateUserRequest(BaseModel):
    first_name: str
    last_name: str
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

@router.post("/", response_model=ServiceResponse[UserData])
def create_user(user_request: CreateUserRequest, session: Session = Depends(get_db)) -> ServiceResponse[UserData]:
    try:
        # Check for duplicate email
        if session.query(User).filter_by(email_address=user_request.email_address).first():
            return ServiceResponse[UserData](
                success=False,
                error="Email address already exists",
                data=[]
            )
        # if session.query(User).filter_by(name=user_request.name).first():
        #     return ServiceResponse[UserData](
        #         success=False,
        #         error="Username already exists",
        #         data=[]
        #     )

        hashed_pw = hash_password(user_request.password)
        # Get next available user_id (auto-increment would be better but this works)
        max_id = session.query(func.max(User.user_id)).scalar() or 0
        next_id = max_id + 1

        start_time = to_utc(user_request.order_notifications_start_date_time)
        interval_days = user_request.days_between_order_notifications or 7
        
        user = User(
            user_id=next_id,
            first_name=user_request.first_name,
            last_name=user_request.last_name,
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
            last_login=datetime.now(UTC),  # Set initial login time at registration
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Convert to UserData model and return structured response
        user_data = UserData.model_validate(user)
        return ServiceResponse[UserData](
            success=True,
            message="User created successfully",
            data=[user_data]
        )
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        # Check for specific constraint violations
        error_str = str(e).lower()
        if "unique" in error_str and "email" in error_str:
            return ServiceResponse[UserData](
                success=False,
                error="Email address already exists",
                data=[]
            )
        elif "unique" in error_str and "name" in error_str:     # will not happen, there is no unique constraint on name in db.
            return ServiceResponse[UserData](
                success=False,
                error="Username already exists",
                data=[]
            )
        else:
            return ServiceResponse[UserData](
                success=False,
                error="Database error occurred",
                data=[]
            )
    except Exception as e:
        session.rollback()
        print(f"Error creating user: {e}")
        return ServiceResponse[UserData](
            success=False,
            error=f"Failed to create user: {str(e)}",
            data=[]
        )


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.put("/{user_id}/password", response_model=ServiceResponse[PasswordUpdateResponse])
def update_user_password(
        user_id: int,
        payload: UpdatePasswordRequest,
        session: Session = Depends(get_db)
) -> ServiceResponse[PasswordUpdateResponse]:
    try:
        # Fetch user
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[PasswordUpdateResponse](
                success=False,
                error=f"User not found",
                data=[]
            )

        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            return ServiceResponse[PasswordUpdateResponse](
                success=False,
                error="Current password is incorrect",
                data=[]
            )

        # Hash and set new password
        new_hashed = hash_password(payload.new_password)
        user.hashed_password = new_hashed
        session.commit()
        session.refresh(user)
        
        password_response = PasswordUpdateResponse(
            user_id=user.user_id,
            password_updated=True
        )
        
        return ServiceResponse[PasswordUpdateResponse](
            success=True,
            message="Password updated successfully",
            data=[password_response]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[PasswordUpdateResponse](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error updating password: {e}")
        return ServiceResponse[PasswordUpdateResponse](
            success=False,
            error=f"Error updating password: {str(e)}",
            data=[]
        )

class UpdateEmailRequest(BaseModel):
    current_password: str
    new_email_address: EmailStr

@router.put("/{user_id}/email", response_model=ServiceResponse[EmailUpdateResponse])
def update_user_email(
        user_id: int,
        payload: UpdateEmailRequest,
        session: Session = Depends(get_db)
) -> ServiceResponse[EmailUpdateResponse]:
    try:
        # Fetch user
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[EmailUpdateResponse](
                success=False,
                error="User not found",
                data=[]
            )

        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            return ServiceResponse[EmailUpdateResponse](
                success=False,
                error="Current password is incorrect",
                data=[]
            )

        # Check for duplicate email (must not already exist)
        existing = session.query(User).filter(
            User.email_address == payload.new_email_address,
            User.user_id != user_id  # Exclude current user
        ).first()
        if existing:
            return ServiceResponse[EmailUpdateResponse](
                success=False,
                error="Email address already exists",
                data=[]
            )

        # Update email
        user.email_address = payload.new_email_address
        session.commit()
        session.refresh(user)
        
        email_response = EmailUpdateResponse(
            user_id=user.user_id,
            email_address=user.email_address
        )
        
        return ServiceResponse[EmailUpdateResponse](
            success=True,
            message="Email address updated successfully",
            data=[email_response]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[EmailUpdateResponse](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error updating email: {e}")
        return ServiceResponse[EmailUpdateResponse](
            success=False,
            error=f"Error updating email address: {str(e)}",
            data=[]
        )

@router.get("/{user_id}", response_model=ServiceResponse[UserData])
def get_user(user_id: int, session: Session = Depends(get_db)) -> ServiceResponse[UserData]:
    try:
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[UserData](
                success=False,
                error="User not found",
                data=[]
            )
        
        user_data = UserData.model_validate(user)
        
        return ServiceResponse[UserData](
            success=True,
            message="User retrieved successfully",
            data=[user_data]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[UserData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error fetching user: {e}")
        return ServiceResponse[UserData](
            success=False,
            error=f"Error fetching user: {str(e)}",
            data=[]
        )


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
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
@router.put("/{user_id}", response_model=ServiceResponse[UserData])
def update_user(user_id: int, payload: UpdateUserRequest, session: Session = Depends(get_db)) -> ServiceResponse[UserData]:
    try:
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[UserData](
                success=False,
                error="User not found",
                data=[]
            )

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
            notification_updated = apply_notification_settings(
                user,
                UpdateNotificationSettingsRequest(**{
                    k: v for k, v in payload.model_dump().items()
                    if k in UpdateNotificationSettingsRequest.model_fields
            })
)
            updated = updated or notification_updated

        if updated:
            session.commit()
            session.refresh(user)
            
            user_data = UserData.model_validate(user)
            
            return ServiceResponse[UserData](
                success=True,
                message="User updated successfully",
                data=[user_data]
            )
        else:
            return ServiceResponse[UserData](
                success=True,
                message="No changes made",
                data=[]
            )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[UserData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        return ServiceResponse[UserData](
            success=False,
            error=f"Error updating user: {str(e)}",
            data=[]
        )


class DeleteUserRequest(BaseModel):
    password: str


@router.delete("/{user_id}", response_model=ServiceResponse[DeleteResponse])
def delete_user(user_id: int, payload: DeleteUserRequest, session: Session = Depends(get_db)) -> ServiceResponse[DeleteResponse]:
    try:
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[DeleteResponse](
                success=False,
                error="User not found",
                data=[]
            )
        
        if not verify_password(payload.password, user.hashed_password):
            return ServiceResponse[DeleteResponse](
                success=False,
                error="Password incorrect",
                data=[]
            )
        
        delete_response = DeleteResponse(
            user_id=user.user_id,
            deleted=True
        )
        
        session.delete(user)
        session.commit()
        
        return ServiceResponse[DeleteResponse](
            success=True,
            message="User deleted successfully",
            data=[delete_response]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[DeleteResponse](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error deleting user: {e}")
        return ServiceResponse[DeleteResponse](
            success=False,
            error=f"Error deleting user: {str(e)}",
            data=[]
        )

class NotificationSettingsResponse(BaseModel):
    days_between_order_notifications: int
    order_notifications_start_date_time: Optional[datetime]
    order_notifications_next_scheduled_time: Optional[datetime]
    order_notifications_via_email: bool
    pending_order_notification: bool

@router.get("/{user_id}/notification-settings", response_model=ServiceResponse[NotificationSettingsData])
def get_notification_settings(user_id: int, session: Session = Depends(get_db)) -> ServiceResponse[NotificationSettingsData]:
    try:
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[NotificationSettingsData](
                success=False,
                error="User not found",
                data=[]
            )

        notification_data = NotificationSettingsData.model_validate(user)
        
        return ServiceResponse[NotificationSettingsData](
            success=True,
            message="Notification settings retrieved successfully",
            data=[notification_data]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[NotificationSettingsData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error fetching notification settings: {e}")
        return ServiceResponse[NotificationSettingsData](
            success=False,
            error=f"Error fetching notification settings: {str(e)}",
            data=[]
        )

# class UpdateNotificationSettingsRequest(BaseModel):
#     days_between_order_notifications: Optional[conint(ge=1, le=365)] = None
#     order_notifications_start_date_time: Optional[datetime] = None
#     order_notifications_via_email: Optional[bool] = None

@router.put("/{user_id}/notification-settings", response_model=ServiceResponse[NotificationSettingsData])
def update_notification_settings(user_id: int, payload: UpdateNotificationSettingsRequest,
                                 session: Session = Depends(get_db)) -> ServiceResponse[NotificationSettingsData]:
    try:
        user = session.get(User, user_id)
        if not user:
            return ServiceResponse[NotificationSettingsData](
                success=False,
                error="User not found",
                data=[]
            )

        updated = apply_notification_settings(user, payload)

        if updated:
            session.commit()
            session.refresh(user)  # Ensure getting fresh DB values
            
            notification_data = NotificationSettingsData.model_validate(user)
            
            return ServiceResponse[NotificationSettingsData](
                success=True,
                message="Notification settings updated successfully",
                data=[notification_data]
            )
        else:
            return ServiceResponse[NotificationSettingsData](
                success=True,
                message="No changes made",
                data=[]
            )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[NotificationSettingsData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error updating notification settings: {e}")
        return ServiceResponse[NotificationSettingsData](
            success=False,
            error=f"Error updating notification settings: {str(e)}",
            data=[]
        )

class LoginRequest(BaseModel):
    email_address: EmailStr
    password: str

@router.post("/login", response_model=ServiceResponse[UserData])
def login_user(payload: LoginRequest, session: Session = Depends(get_db)) -> ServiceResponse[UserData]:
    try:
        user = authenticate_user(payload.email_address, payload.password, session)
        if not user:
            return ServiceResponse[UserData](
                success=False,
                error="Invalid email or password",
                data=[]
            )

        user.last_login = datetime.now(UTC)
        user.last_notification_sent_at = datetime.now(UTC)

        # Check if user has an active cart
        active_cart = session.query(Cart).filter(
            Cart.user_id == user.user_id
        ).order_by(Cart.updated_at.desc()).first()

        session.commit()
        session.refresh(user)

        user_data = UserData.model_validate(user)
        user_data.has_active_cart = active_cart is not None
        
        return ServiceResponse[UserData](
            success=True,
            message="Login successful",
            data=[user_data]
        )
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[UserData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error during login: {e}")
        return ServiceResponse[UserData](
            success=False,
            error=f"Login failed: {str(e)}",
            data=[]
        )

class OrderStatusNotification(BaseModel):
    order_id: int
    status: str
    changed_at: datetime

@router.get("/{user_id}/order-status-notifications", response_model=ServiceResponse[OrderStatusNotification])
def get_order_status_notifications(
    user_id: int,
    session: Session = Depends(get_db)
):
    user = session.get(User, user_id)
    if not user:
        return ServiceResponse[OrderStatusNotification](
            success=False,
            error="User not found",
            data=[]
        )
    
    # Use last_notifications_viewed_at when available
    since = user.last_notifications_viewed_at or datetime.min.replace(tzinfo=UTC)

    # Follow filter -> join -> group strategy to get order status updates

    # Create subquery to get max changed_at per order
    subquery = session.query(
        OrderStatusHistory.order_id,
        func.max(OrderStatusHistory.changed_at).label('max_changed_at')
    ).join(Order).filter(
        Order.user_id == user_id,
        OrderStatusHistory.changed_at > since
    ).group_by(OrderStatusHistory.order_id).subquery()

    # Get full status history records for the max timestamps
    status_changes = session.query(OrderStatusHistory).join(
        subquery,
        and_(
            OrderStatusHistory.order_id == subquery.c.order_id,
            OrderStatusHistory.changed_at == subquery.c.max_changed_at
        )
    ).all()

    # Update last_notifications_viewed_at to current time
    user.last_notifications_viewed_at = datetime.now(UTC)
    session.commit()

    return ServiceResponse[OrderStatusNotification](
        success=True,
        message="Order status notifications read successfully",
        data=[OrderStatusNotification(
            order_id=change.order_id,
            status=change.new_status.value,
            changed_at=change.changed_at
        )
        for change in status_changes]
    )
