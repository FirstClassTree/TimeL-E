# backend/app/routers/orders.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from ..models.base import APIResponse
from ..services.database_service import db_service
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

router = APIRouter(prefix="/orders", tags=["Orders"])

class OrderItemRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    product_id: int
    quantity: int = 1

class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    external_user_id: str
    items: List[OrderItemRequest]

@router.get("/user/{external_user_id}", response_model=APIResponse)
async def get_user_orders(
    external_user_id: str,
    limit: int = Query(20, description="Number of orders to return", ge=1, le=100),
    offset: int = Query(0, description="Number of orders to skip", ge=0)
) -> APIResponse:
    """Get order history for a specific user with items included"""
    try:
        # Get user orders using the generic entity approach
        db_result = await db_service.get_entity("orders", f"user/{external_user_id}")
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        orders_data = db_result.get("data", [])
        
        if not orders_data:
            return APIResponse(
                message=f"No orders found for user {external_user_id}",
                data={"orders": [], "total": 0, "has_next": False}
            )
        
        # Group the data by order_id since SQL JOIN returns multiple rows
        orders_map = {}
        
        for row in orders_data:
            order_id = row["order_id"]
            
            if order_id not in orders_map:
                orders_map[order_id] = {
                    "order_id": order_id,
                    "user_id": row["user_id"],
                    "order_number": row["order_number"],
                    "status": row["status"],
                    "total_items": row["total_items"],
                    "items": []
                }
            
            # Add item if it exists (handles orders without items)
            if row.get("product_id"):
                orders_map[order_id]["items"].append({
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "quantity": row["quantity"]
                })
        
        # Convert to list and sort by order_number descending
        orders_list = list(orders_map.values())
        orders_list.sort(key=lambda x: x["order_number"], reverse=True)
        
        return APIResponse(
            message=f"Found {len(orders_list)} orders for user {external_user_id}",
            data={
                "orders": orders_list,
                "total": len(orders_list),
                "page": (offset // limit) + 1,
                "per_page": limit,
                "has_next": len(orders_list) == limit,
                "has_prev": offset > 0
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=APIResponse)
async def create_order(order_request: CreateOrderRequest) -> APIResponse:
    """Create a new order with items"""
    try:
        if not order_request.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")
        
        # Validate user exists using generic entity approach
        user_result = await db_service.get_entity("users", order_request.external_user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=400, detail=f"User {order_request.external_user_id} not found")
        
        # Validate all products exist
        for item in order_request.items:
            product_result = await db_service.get_product_by_id(item.product_id)
            if not product_result.get("success", True) or not product_result.get("data", []):
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        # Create the order using generic entity approach
        create_result = await db_service.create_entity("orders", {
            "external_user_id": order_request.external_user_id,
            "items": [item.model_dump() for item in order_request.items]
        })
        
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
