# db_service/app/db_core/models/orders.py

"""
orders.py

SQLAlchemy ORM models for the orders schema, including orders, order items,
shopping carts, and cart items. Models define business logic constraints, relationships,
and metadata for use in API, admin, and business logic layers.
"""

from sqlalchemy import Integer, String, ForeignKey, LargeBinary, TIMESTAMP, CheckConstraint, Text, Index, Float, Uuid, text
from sqlalchemy.types import BigInteger
from sqlalchemy import Enum as SqlEnum
from typing import Optional
from .base import Base
from . import User, Product
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from datetime import datetime, UTC

class OrderStatus(enum.Enum):
    """
    Enum representing the lifecycle status of an order.

    OpenAPI Description:
        Possible values:
            - pending: Order created but not processed
            - processing: Order is being processed (e.g. payment or fulfillment in progress)
            - shipped: Order has shipped
            - delivered: Order delivered to customer
            - cancelled: Order cancelled before fulfillment
            - failed: Order failed (e.g. payment or delivery issue)
            - return_requested: Customer requested a return
            - returned: Order returned and processed
            - refunded: Payment refunded
    """
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"                 # Order was canceled before fulfillment
    FAILED = "failed"                       # Order failed (e.g., payment issue)
    RETURN_REQUESTED = "return_requested"   # Customer requested return
    RETURNED = "returned"                   # Returned and processed
    REFUNDED = "refunded"                   # Payment has been refunded

OrderStatusEnum = SqlEnum(
    OrderStatus,
    name="order_status_enum",
    values_callable=lambda x: [e.value for e in x]
)

class Order(Base):
    """
    Database model for a customer's placed order.

    Stores metadata about a customer's order, delivery details,
    and links to all associated order items.

        Attributes:
        id (int): Primary key order ID (exposed to clients as string).
        user_id (int): Internal user ID who placed the order (foreign key to users.id).
        order_number (int): Sequential order number for this user.
        order_dow (int): Day of week order was placed (0=Sunday, 6=Saturday).
        order_hour_of_day (int): Hour of day order was placed (0-23).
        days_since_prior_order (Optional[int]): Days since user's prior order.
        total_items (int): Total items in this order.
        status (OrderStatus): Current order status (enum).
        phone_number (Optional[str]): Delivery contact phone.
        street_address (Optional[str]): Delivery address street.
        city (Optional[str]): Delivery city.
        postal_code (Optional[str]): Delivery postal/ZIP code.
        country (Optional[str]): Delivery country.
        tracking_number (Optional[str]): Shipping tracking number.
        shipping_carrier (Optional[str]): Shipping provider/carrier.
        tracking_url (Optional[str]): URL for tracking shipment.
        invoice (Optional[bytes]): Invoice file (PDF/image, optional).
        created_at (datetime): When the order was created (UTC).
        updated_at (datetime): When the order was last updated (UTC).
        user (User): The user who placed this order (relationship).
        order_items (List[OrderItem]): List of items in this order (relationship).

    Relationships:
        - user: The User who placed this order
        - order_items: All items purchased in this order

    OpenAPI Description:
        Database table for customer orders, including contact, shipping, and tracking details.
    """
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint('total_items >= 0', name='ck_order_total_items_nonnegative'),
        CheckConstraint('total_price >= 0', name='ck_order_total_price_nonnegative'),
        Index('ix_orders_userid_orderid', 'user_id', 'id'),   # for order status notifications
        {"schema": "orders"}
    )

    # Primary key order ID (exposed to clients as string)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign key to internal user ID (references users.id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.users.id'), index=True, nullable=False)
    # eval_set: Mapped[str] = mapped_column(String())
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    order_dow: Mapped[int] = mapped_column(Integer, nullable=False)
    order_hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)
    days_since_prior_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(OrderStatusEnum,
                                                 default=OrderStatus.PENDING, nullable=False)

    # Optional delivery and invoice details
    delivery_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    street_address:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city:  Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code:  Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country:  Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number:  Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_carrier:  Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tracking_url:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice:  Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)  # e.g. PDF or image blob

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),   # ensures it maps to PostgreSQL's `timestamptz`
        default=lambda: datetime.now(UTC),
        nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable = False)

    # Enables accessing the user associated with the order through ORM relationship
    user: Mapped["User"]  = relationship(
        "User",
        back_populates="orders",
        doc="The user associated with this order.")

    # Sets up automatic lazy-loading of order items related to an order via foreign key
    order_items: Mapped[list["OrderItem"]]  = relationship(
        "OrderItem", back_populates="order",
        cascade="all, delete-orphan",
        doc="List of all order items associated with this order.")

    @property
    def items(self) -> list["OrderItem"]:
        """
        Returns a list of all OrderItem objects belonging to this order.

        OpenAPI Description:
            Read-only shortcut for accessing all items in this order.
        """
        return self.order_items


class OrderItem(Base):
    """
    Represents a single item/product in an order.

    Attributes:
        - order_id: ID of the order this item belongs to
        - product_id: ID of the product
        - add_to_cart_order: Sequential order in which this item was added to the order
        - reordered: Boolean as int (0 or 1), if item was reordered from prior order
        - quantity: Number of units ordered

    Relationships:
        - order: The parent Order
        - product: The Product purchased

    OpenAPI Description:
        Join table for orders and products. Enforces constraints to ensure integrity.
    """
    __tablename__ = 'order_items'
    __table_args__ = (
        CheckConstraint('reordered IN (0, 1)', name='ck_orderitem_reordered_bool'),
        CheckConstraint('add_to_cart_order >= 0', name='ck_orderitem_add_to_cart_order_nonnegative'),
        CheckConstraint('quantity > 0', name='ck_orderitem_quantity_positive'),
        CheckConstraint('price >= 0', name='ck_orderitem_price_nonnegative'),
        {"schema": "orders"}
    )

    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('orders.orders.id'), primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.products.product_id'), primary_key=True, index=True)
    add_to_cart_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reordered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Enables navigating back to the order this item belongs to
    order: Mapped["Order"]  = relationship(
        "Order", back_populates="order_items",
        doc="The parent order to which this item belongs.")

    # Enables accessing the product associated with this order item through ORM relationship
    product: Mapped["Product"] = relationship(
        "Product",
        doc="The product associated with this order item.")

class Cart(Base):
    """
    Shopping cart for a user, storing items added before checkout.

    Attributes:
        - id: Primary key cart ID (exposed to clients as string)
        - user_id: Internal user ID who owns this cart (foreign key to users.id)
        - total_items: Total items in the cart
        - created_at: When the cart was created
        - updated_at: When the cart was last updated

    Relationships:
        - user: The user who owns this cart
        - cart_items: Items currently in this cart

    OpenAPI Description:
        Table representing a user's active or historical cart state.
    """
    __tablename__ = 'carts'
    __table_args__ = (
        CheckConstraint('total_items >= 0', name='ck_cart_total_items_nonnegative'),
        {"schema": "orders"}
    )

    # Primary key cart ID (exposed to clients as string)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign key to internal user ID (references users.id)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.users.id'), index=True, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                          default=lambda: datetime.now(UTC),
                                                          nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                          default=lambda: datetime.now(UTC),
                                                          onupdate=lambda: datetime.now(UTC),
                                                          nullable = False)

    # Enables accessing the user associated with the cart through ORM relationship
    user: Mapped["User"]  = relationship(
        "User", back_populates="carts",
        doc="The user associated with this cart.")

    # Sets up automatic lazy-loading of cart items related to a cart via foreign key
    cart_items: Mapped[list["CartItem"]]  = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        doc="List of all items currently in this cart.")

    @property
    def items(self) -> list["CartItem"]:
        """
        Returns all CartItem objects in this cart.

        OpenAPI Description:
            Read-only shortcut for accessing all items in this cart.
        """
        return self.cart_items


class CartItem(Base):
    """
    Represents a single product in a shopping cart.

    Attributes:
        - cart_id: ID of the cart this item belongs to
        - product_id: ID of the product
        - add_to_cart_order: Sequential order in which this item was added to the cart
        - reordered: Boolean as int (0 or 1), if item was reordered from prior order
        - quantity: Number of units ordered

    Relationships:
        - cart: Parent Cart object
        - product: Product being added

    OpenAPI Description:
        Join table for cart and products. Enforces constraints to ensure integrity.
    """

    __tablename__ = 'cart_items'
    __table_args__ = (
        CheckConstraint('reordered IN (0, 1)', name='ck_cartitem_reordered_bool'),
        CheckConstraint('add_to_cart_order >= 0', name='ck_cartitem_add_to_cart_order_nonnegative'),
        CheckConstraint('quantity > 0', name='ck_cartitem_quantity_positive'),
        {"schema": "orders"}
    )

    cart_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('orders.carts.id'), primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.products.product_id'), primary_key=True, index=True)
    add_to_cart_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reordered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Enables navigating back to the order this item belongs to
    cart: Mapped["Cart"] = relationship(
        "Cart",
        back_populates="cart_items",
        doc="The cart to which this item belongs.")

    # Enables accessing the product associated with this order item through ORM relationship
    product: Mapped["Product"] = relationship(
        "Product",
        doc="The product associated with this cart item.")


class OrderStatusHistory(Base):
    """
    Database model for tracking changes to order statuses.

    Stores a history of status changes for orders, including who made the change
    and any relevant notes.

    Attributes:
        history_id (int): Unique history identifier (primary key).
        order_id (int): Order that was changed (foreign key).
        old_status (str): Previous status of the order.
        new_status (str): New status of the order.
        changed_at (datetime): When the change occurred (UTC).
        changed_by (int): Optional user or system identifier who made the change.
        note (str): Optional note about the change.

    Relationships:
        - order: The Order associated with this status change

    OpenAPI Description:
        Audit table for tracking order status changes over time.
    """
    __tablename__ = 'order_status_history'
    __table_args__ = (
        Index('ix_orderstatushistory_orderid_changedat', 'order_id', 'changed_at'),   # for order status notifications
        {"schema": "orders"}
    )
    
    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('orders.orders.id'), index=True)
    old_status: Mapped[Optional[OrderStatus]] = mapped_column(OrderStatusEnum,
                                                      default=OrderStatus.PENDING, nullable=True)
    new_status: Mapped[OrderStatus] = mapped_column(OrderStatusEnum,
                                            default=OrderStatus.PENDING, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now(UTC), index=True)
    changed_by: Mapped[Optional[Uuid]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Enables accessing the order associated with this status change
    order: Mapped["Order"] = relationship(
        "Order",
        doc="The order associated with this status change.")
