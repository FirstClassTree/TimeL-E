# backend/app/models/grocery.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from pydantic.alias_generators import to_camel

class Product(BaseModel):
    """Product model matching CSV structure"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

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
    """Department model matching frontend TypeScript interface"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    id: str
    name: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    parentId: Optional[str] = None

class Aisle(BaseModel):
    """Aisle model"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    aisle_id: int
    aisle: str

class Order(BaseModel):
    """Order model matching CSV structure"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    order_id: str  # Changed to str to match UUID
    user_id: str  # Changed to str to match UUID
    eval_set: str
    order_number: int
    order_dow: int  # day of week (0-6)
    order_hour_of_day: int
    days_since_prior_order: Optional[float] = None

class OrderItem(BaseModel):
    """Order item model matching CSV structure"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    order_id: str  # Changed to str to match UUID
    product_id: int
    add_to_cart_order: int  # sequence in cart
    reordered: int  # 0 or 1
    quantity: int = 1  # Added quantity field
    # Joined data for frontend convenience
    product_name: Optional[str] = None

class OrderWithItems(BaseModel):
    """Order with its items for detailed view"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    user_id: str  # Changed to str to match UUID
    items: List[dict]  # [{"product_id": 123, "quantity": 2}, ...]

class ProductSearchResult(BaseModel):
    """Product search result with pagination info"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    products: List[Product]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class PredictionItem(BaseModel):
    """Individual prediction item"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    product_id: int
    product_name: str
    score: float

class UserPredictions(BaseModel):
    """User prediction response"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    user_id: str  # Changed to str to match UUID
    predictions: List[PredictionItem]
    total: int

class OrderItemResponse(BaseModel):
    """Order item response model for API responses"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    order_id: Optional[str] = None  # Not always provided in item data
    product_id: int
    add_to_cart_order: int
    reordered: int
    quantity: int
    product_name: Optional[str] = None
    aisle_name: Optional[str] = None
    department_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None

class OrderResponse(BaseModel):
    """Order response model for API responses - matches actual database structure"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    order_id: str
    user_id: str
    order_number: int
    total_items: int
    total_price: Optional[float] = None
    status: str
    delivery_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    created_at: Optional[str] = None  # Keep as string to match database format
    updated_at: Optional[str] = None  # Keep as string to match database format
    items: List[OrderItemResponse] = []
