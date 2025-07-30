# pydantic_models.py

from pydantic import BaseModel, Field, EmailStr, constr
from typing import Optional, List
import datetime
import enum

# ----- Enum -----
class OrderStatus(str, enum.Enum):
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
    CANCELLED = "cancelled"
    FAILED = "failed"
    RETURN_REQUESTED = "return_requested"
    RETURNED = "returned"
    REFUNDED = "refunded"

# ----- User -----
class User(BaseModel):
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
    first_name: str = Field(..., description="User's first name (not required to be unique)")
    last_name: str = Field(..., description="User's last name (not required to be unique)")
    hashed_password: str = Field(..., description="Securely hashed password for authentication")
    email_address: EmailStr = Field(..., description="User's unique email address")
    phone_number: Optional[str] = Field(None, description="User's contact phone number. May be null if not provided")
    street_address: Optional[str] = Field(None, description="Primary delivery street address. Nullable")
    city: Optional[str] = Field(None, description="City for delivery address. Nullable")
    postal_code: Optional[str] = Field(None, description="Postal or ZIP code for delivery. Nullable")
    country: Optional[str] = Field(None, description="Country for delivery address. Nullable")

    class Config:
        from_attributes = True

# ----- Product -----
class Product(BaseModel):
    """
    Master table for products.

    Attributes:
        product_id (int): Primary key.
        product_name (str): Name of product.
        aisle_id (int): Foreign key to aisle.
        department_id (int): Foreign key to department.

    Relationships:
        - department: Department to which product belongs.
        - aisle: Aisle to which product belongs.
        - order_items: Order items containing this product.
        - enriched: Enriched product metadata (one-to-one relationship).

    OpenAPI Description:
        Products available in the catalog, with classification by aisle and department.
    """
    product_name: str = Field(..., description="Name of the product")
    aisle_id: int = Field(..., description="Foreign key to aisle")
    department_id: int = Field(..., description="Foreign key to department")

    class Config:
        from_attributes = True

class Department(BaseModel):
    """
    Model for department (product classification).

    Attributes:
        department_id (int): Unique department identifier (primary key).
        department (str): Name of the department.
    """
    department_id: int
    department: str

    class Config:
        from_attributes = True

class Aisle(BaseModel):
    """
    Product aisle (e.g., 'Baking Ingredients', 'Fresh Herbs').

    Attributes:
        aisle_id (int): Primary key.
        aisle (str): Name of aisle.

    Relationships:
        - products: All products in this aisle.

    OpenAPI Description:
        Catalog table for physical or logical product aisles.
    """
    aisle_id: int
    aisle: str

    class Config:
        from_attributes = True

class ProductEnriched(BaseModel):
    """
    Enriched metadata for a product.

    Attributes:
        product_id (int): Product primary key (FK).
        description (str): Optional human-friendly description.
        price (float): Price of product. Defaults to 0.00.
        image_url (str): Optional image URL.

    Relationships:
        - product: Main Product object (one-to-one relationship).

    OpenAPI Description:
        Additional metadata for products, including description, price, and imagery.
    """
    product_id: int
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# ----- Orders -----
class OrderItem(BaseModel):
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
    order_id: int
    product_id: int
    add_to_cart_order: int = 0
    reordered: int = 0
    quantity: int = 1

    class Config:
        from_attributes = True

class CartItem(BaseModel):
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
    cart_id: int
    product_id: int
    add_to_cart_order: int = 0
    reordered: int = 0
    quantity: int = 1

    class Config:
        from_attributes = True

class Cart(BaseModel):
    """
    Shopping cart for a user, storing items added before checkout.

    Attributes:
        - cart_id: Primary key
        - user_id: Foreign key to user
        - total_items: Total items in the cart
        - created_at: When the cart was created
        - updated_at: When the cart was last updated

    Relationships:
        - user: The user who owns this cart
        - cart_items: Items currently in this cart

    OpenAPI Description:
        Table representing a user's active or historical cart state.
    """
    cart_id: int
    user_id: int
    total_items: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    cart_items: Optional[List[CartItem]] = None

    class Config:
        from_attributes = True

class Order(BaseModel):
    """
    Database model for a customer's placed order.

    Stores metadata about a customer's order, delivery details,
    and links to all associated order items.

        Attributes:
        order_id (int): Unique order identifier (primary key).
        user_id (int): User who placed the order (foreign key).
        order_number (int): Sequential order number for this user.
        order_dow (int): Day of week order was placed (0=Sunday, 6=Saturday).
        order_hour_of_day (int): Hour of day order was placed (0–23).
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
    order_id: int
    user_id: int
    order_number: int
    order_dow: int
    order_hour_of_day: int
    days_since_prior_order: Optional[int] = None
    total_items: int
    status: OrderStatus
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    invoice: Optional[bytes] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    order_items: Optional[List[OrderItem]] = None

    class Config:
        from_attributes = True
