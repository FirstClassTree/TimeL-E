# db_service/app/models/orders.py

from sqlalchemy import Integer, String, Float, ForeignKey, LargeBinary
from sqlalchemy import Enum as SqlEnum
from typing import Optional
from app.models.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
# from uuid import uuid7   # native uuid7 in python 3.14
from uuid_utils import uuid7
import enum

class OrderStatus(enum.Enum):
    """ represents the lifecycle status of an order """
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"                 # Order was canceled before fulfillment
    FAILED = "failed"                       # Order failed (e.g., payment issue)
    RETURN_REQUESTED = "return_requested"   # Customer requested return
    RETURNED = "returned"                   # Returned and processed
    REFUNDED = "refunded"                   # Payment has been refunded

class Order(Base):
    """ tracks order metadata """
    __tablename__ = 'orders'
    __table_args__ = {"schema": "orders"}

    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.users.user_id'), index=True)
    eval_set: Mapped[str] = mapped_column(String())
    order_number: Mapped[int] = mapped_column(Integer)
    order_dow: Mapped[int] = mapped_column(Integer)
    order_hour_of_day: Mapped[int] = mapped_column(Integer)
    days_since_prior_order: Mapped[Optional[float]] = mapped_column(Float)
    total_items: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(SqlEnum(OrderStatus, name="order_status_enum"),
                                                 default=OrderStatus.PENDING, nullable=False)

    # Optional delivery and invoice details
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    street_address: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str] = mapped_column(String(100), nullable=True)
    shipping_carrier: Mapped[str] = mapped_column(String(50), nullable=True)
    tracking_url: Mapped[str] = mapped_column(String(255), nullable=True)
    invoice: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)  # e.g. PDF or image blob

    # Enables accessing the user associated with the order through ORM relationship
    user = relationship("User", back_populates="orders")

    # Sets up automatic lazy-loading of order items related to an order via foreign key
    order_items = relationship("OrderItem", back_populates="order")

    @property
    def items(self):
        return self.order_items


class OrderItem(Base):
    """ tracks the individual items in each order """
    __tablename__ = 'order_items'
    __table_args__ = {"schema": "orders"}

    order_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('orders.orders.order_id'), primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.products.product_id'), primary_key=True, index=True)
    add_to_cart_order: Mapped[int] = mapped_column(Integer)
    reordered: Mapped[int] = mapped_column(Integer)
    # product_name: Mapped[str] = mapped_column(String(), ForeignKey('products.products.product_name'))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Enables navigating back to the order this item belongs to
    order = relationship("Order", back_populates="order_items")

    # Enables accessing the product associated with this order item through ORM relationship
    product = relationship("Product")