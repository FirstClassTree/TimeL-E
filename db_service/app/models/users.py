# db_service/app/models/users.py

# from uuid import uuid7   # native uuid7 in python 3.14
from uuid_utils import uuid7
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"schema": "users"}

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7, unique=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    email_address: Mapped[str] = mapped_column(String, unique=True, index=True)     # indexed for login

    # Contact and delivery details
    phone_number: Mapped[str] = mapped_column(String(20))
    street_address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100))

    # Enables accessing all orders by this user
    orders = relationship("Order", back_populates="user")
