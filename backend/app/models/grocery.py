# backend/app/models/grocery.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Product(BaseModel):
    """Product model matching CSV structure"""
    product_id: int
    product_name: str
    aisle_id: int
    department_id: int
    # Joined data for frontend convenience
    aisle_name: Optional[str] = None
    department_name: Optional[str] = None
    # Enriched data from product_enriched table
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None

class Department(BaseModel):
    """Department model"""
    department_id: int
    department: str

class Aisle(BaseModel):
    """Aisle model"""
    aisle_id: int
    aisle: str

class Order(BaseModel):
    """Order model matching CSV structure"""
    order_id: str  # Changed to str to match UUID
    user_id: str  # Changed to str to match UUID
    eval_set: str
    order_number: int
    order_dow: int  # day of week (0-6)
    order_hour_of_day: int
    days_since_prior_order: Optional[float] = None

class OrderItem(BaseModel):
    """Order item model matching CSV structure"""
    order_id: str  # Changed to str to match UUID
    product_id: int
    add_to_cart_order: int  # sequence in cart
    reordered: int  # 0 or 1
    quantity: int = 1  # Added quantity field
    # Joined data for frontend convenience
    product_name: Optional[str] = None

class OrderWithItems(BaseModel):
    """Order with its items for detailed view"""
    order_id: str  # Changed to str to match UUID
    user_id: str  # Changed to str to match UUID
    eval_set: str
    order_number: int
    order_dow: int
    order_hour_of_day: int
    days_since_prior_order: Optional[float] = None
    total_items: int = 0
    status: Optional[str] = None
    # Delivery/tracking fields
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    items: List[OrderItem] = []

class CreateOrderRequest(BaseModel):
    """Request model for creating new orders"""
    user_id: str  # Changed to str to match UUID
    items: List[dict]  # [{"product_id": 123, "quantity": 2}, ...]

class ProductSearchResult(BaseModel):
    """Product search result with pagination info"""
    products: List[Product]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class PredictionItem(BaseModel):
    """Individual prediction item"""
    product_id: int
    product_name: str
    score: float

class UserPredictions(BaseModel):
    """User prediction response"""
    user_id: str  # Changed to str to match UUID
    predictions: List[PredictionItem]
    total: int
