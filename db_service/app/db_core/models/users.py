# db_service/app/db_core/models/users.py

"""
users.py

SQLAlchemy ORM models for the users schema.

Defines the User table, including login credentials, contact, and delivery details.
Also defines relationships to orders and carts. The model defines relationships
and metadata for use in API, admin, and business logic layers.

OpenAPI Description:
    Represents a user account with authentication credentials, optional contact and delivery info,
    and relationships to order and cart records.
"""

from sqlalchemy import String, Integer,TIMESTAMP, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta, UTC
from .base import Base
from typing import List, Optional

class User(Base):
    """
    Database model for registered users.

    Stores a user account, authentication credentials, and optional contact/delivery details,
    and links to all associated orders and carts.

    Attributes:
        user_id (int): Unique identifier for the user (primary key).
        first_name (str): User's first name (not required to be unique).
        last_name (str): User's last name (not required to be unique).
        hashed_password (str): Securely hashed password for authentication.
        email_address (str): User's unique email address. Used for login and account recovery.
        phone_number (Optional[str]): User's contact phone number. May be null if not provided.
        street_address (Optional[str]): Primary delivery street address. Nullable.
        city (Optional[str]): City for delivery address. Nullable.
        postal_code (Optional[str]): Postal or ZIP code for delivery. Nullable.
        country (Optional[str]): Country for delivery address. Nullable.
        orders (List[Order]): List of all orders placed by this user.
        carts (List[Cart]): List of all shopping carts owned by this user.
        last_notification_sent_at (Mapped[Optional[datetime]]): last time a notification was triggered.


    Relationships:
        - orders: List of all orders placed by this user.
        - carts: List of all shopping carts owned by this user.

    OpenAPI Description:
        User account table, storing login credentials (hashed password and unique email),
        and optional contact and delivery details. Provides access to orders and shopping carts
        for business logic and user-facing APIs.

    Example:
        User(
            user_id=1,
            first_name="Alice",
            last_name="Smith",
            hashed_password="$2b$12$...",
            email_address="alice@example.com",
            phone_number="555-1234",
            street_address="123 Main St",
            city="Metropolis",
            postal_code="12345",
            country="USA")
    """
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint(
            "(days_between_order_notifications IS NULL OR (days_between_order_notifications >= 1 AND days_between_order_notifications <= 365))",
            name="check_days_between_order_notifications"
        ),
        {"schema": "users"}
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)     # allow repeating names
    last_name: Mapped[str] = mapped_column(String, nullable=False)      # allow repeating names
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    email_address: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)     # indexed for fast login

    # Contact and delivery details
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    street_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Last login timestamp
    last_login: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True),
                                                           default=None,
                                                           nullable=True)

    # Last accessed /users/{user_id}/order-status-notifications
    last_notifications_viewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True),
                                                                             nullable=True,
                                                                             doc="When the user last viewed their order status notifications.")

    # Notification for order scheduling
    days_between_order_notifications: Mapped[Optional[int]] = mapped_column(Integer, default=7, nullable=True)

    order_notifications_start_date_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True),
                                                      default=lambda: datetime.now(UTC),
                                                      nullable=True)

    order_notifications_next_scheduled_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True),
                                                          default=lambda: datetime.now(UTC)  + timedelta(days=7),
                                                          nullable=True)

    last_notification_sent_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True),
                                                          default=None,
                                                          nullable=True)

    pending_order_notification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    order_notifications_via_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


    # Enables accessing all orders by this user
    orders: Mapped[List["Order"]]  = relationship("Order", back_populates="user")

    # Enables accessing all carts by this user
    carts: Mapped[List["Cart"]] = relationship("Cart", back_populates="user")
