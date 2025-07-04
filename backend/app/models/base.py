# backend/app/models/base.py
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from datetime import datetime

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None
    timestamp: datetime = datetime.now()

class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class GenericEntity(BaseModel):
    """Generic entity for flexible JSON handling"""
    id: Optional[str] = None
    data: Dict[str, Any]

class ServiceRequest(BaseModel):
    """Generic service request"""
    endpoint: str
    method: str = "GET"
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None

class CartItem(BaseModel):
    """Cart item model"""
    item_id: str
    quantity: int
    price: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class Cart(BaseModel):
    """Cart model"""
    user_id: str
    items: List[CartItem] = []
    total_price: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class Order(BaseModel):
    """Order model"""
    user_id: str
    cart_id: Optional[str] = None
    items: List[CartItem]
    total_price: float
    delivery_time: Optional[datetime] = None
    status: str = "pending"
    metadata: Optional[Dict[str, Any]] = None
