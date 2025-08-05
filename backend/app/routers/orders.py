# backend/app/routers/orders.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from ..models.base import APIResponse
from ..services.database_service import db_service
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

router = APIRouter(prefix="/orders", tags=["Orders"])

class OrderItemRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    product_id: int
    quantity: int = 1
    add_to_cart_order: Optional[int] = None
    reordered: int = 0

class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    user_id: str
    order_dow: Optional[int] = None
    order_hour_of_day: Optional[int] = None
    days_since_prior_order: Optional[int] = None
    total_items: Optional[int] = None
    # status is always "pending" for new orders - not configurable by client
    delivery_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    items: List[OrderItemRequest]

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_orders(
    user_id: str,
    limit: int = Query(20, description="Number of orders to return", ge=1, le=100),
    offset: int = Query(0, description="Number of orders to skip", ge=0)
) -> APIResponse:
    """Get order history for a specific user with items included"""
    try:
        # with proper pagination and enriched data
        db_result = await db_service.get_entity("orders", f"user/{user_id}", f"?limit={limit}&offset={offset}")
        
        if not db_result.get("success", True):
            error_msg = db_result.get("error", "Database query failed")
            if "User not found" in error_msg:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            print(f"Get orders for user {user_id} failed: {error_msg}")
            raise HTTPException(status_code=500, detail=f"An internal server error occurred while retrieving orders for user {user_id}")
        
        orders_data = db_result.get("data", [])
        
        if not orders_data:
            return APIResponse(
                message=f"No orders found for user {user_id}",
                data={"orders": [], "total": 0, "has_next": False}
            )
        
        # The db_service now returns properly structured data, no grouping needed
        return APIResponse(
            message=f"Found {len(orders_data)} orders for user {user_id}",
            data={
                "orders": orders_data,
                "total": len(orders_data),
                "page": (offset // limit) + 1,
                "per_page": limit,
                "has_next": len(orders_data) == limit,
                "has_prev": offset > 0
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=APIResponse)
async def get_order_details(order_id: str) -> APIResponse:
    """Get detailed order information with full tracking info, enriched products, and status history"""
    try:
        # Use db_service endpoint for detailed order view
        db_result = await db_service.get_entity("orders", order_id)
        
        if not db_result.get("success", True):
            error_msg = db_result.get("error", "Database query failed")
            if "Order not found" in error_msg:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            if "Invalid order ID format" in error_msg:
                raise HTTPException(status_code=400, detail="Invalid order ID format")
            print(f"Get order details for {order_id} failed: {error_msg}")
            raise HTTPException(status_code=500, detail=f"An internal server error occurred while retrieving order {order_id}")
        
        order_data = db_result.get("data", [])
        
        if not order_data:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        # The db_service returns a list, get the first item
        order = order_data[0]
        
        return APIResponse(
            message=f"Order {order_id} details retrieved successfully",
            data=order
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting order details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=APIResponse)
async def create_order(order_request: CreateOrderRequest) -> APIResponse:
    """Create a new order with items"""
    try:
        if not order_request.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")
        
        # Validate user exists using generic entity approach
        user_result = await db_service.get_entity("users", order_request.user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=400, detail=f"User {order_request.user_id} not found")
        
        # Validate all products exist
        for item in order_request.items:
            product_result = await db_service.get_product_by_id(item.product_id)
            if not product_result.get("success", True) or not product_result.get("data", []):
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        # Set total_items if not provided
        if order_request.total_items is None:
            order_request.total_items = len(order_request.items)
        
        # Create the order using generic entity approach
        # Send the complete request data
        create_result = await db_service.create_entity("orders", order_request.model_dump(exclude_unset=True))
        
        if not create_result.get("success", True):
            error_detail = create_result.get("error", "Failed to create order")
            raise HTTPException(status_code=500, detail=error_detail)
        
        order_data = create_result.get("data", {})
        
        return APIResponse(
            message="Order created successfully",
            data=order_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
