# db_service/app/models/users.py

from sqlalchemy import String, Integer
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"schema": "users"}

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    email_address: Mapped[str] = mapped_column(String, unique=True, index=True)     # indexed for login

    # Contact and delivery details
    phone_number: Mapped[str] = mapped_column(String(50))
    street_address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100))

    # Enables accessing all orders by this user
    orders = relationship("Order", back_populates="user")
