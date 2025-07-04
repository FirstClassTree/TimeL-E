# backend/app/routers/orders.py
from fastapi import APIRouter, HTTPException
from typing import List
from ..models.base import APIResponse
from ..models.grocery import Order, OrderWithItems, CreateOrderRequest
from ..services.mock_data import mock_data

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_orders(user_id: int) -> APIResponse:
    """Get all orders for a specific user"""
    try:
        orders = mock_data.get_user_orders(user_id)
        
        if not orders:
            return APIResponse(
                message=f"No orders found for user {user_id}",
                data={"orders": [], "total": 0}
            )
        
        # Add item counts to each order
        orders_with_counts = []
        for order in orders:
            items = mock_data.get_order_items(order.order_id)
            order_dict = order.dict()
            order_dict["item_count"] = len(items)
            orders_with_counts.append(order_dict)
        
        return APIResponse(
            message=f"Found {len(orders)} orders for user {user_id}",
            data={
                "orders": orders_with_counts,
                "total": len(orders)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=APIResponse)
async def get_order(order_id: int) -> APIResponse:
    """Get specific order with all its items"""
    try:
        order_with_items = mock_data.get_order_with_items(order_id)
        
        if not order_with_items:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return APIResponse(
            message="Order retrieved successfully",
            data=order_with_items
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/items", response_model=APIResponse)
async def get_order_items(order_id: int) -> APIResponse:
    """Get items for a specific order"""
    try:
        # Verify order exists
        order = mock_data.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        items = mock_data.get_order_items(order_id)
        
        return APIResponse(
            message=f"Found {len(items)} items in order {order_id}",
            data={
                "order_id": order_id,
                "items": items,
                "total_items": len(items)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=APIResponse)
async def create_order(order_request: CreateOrderRequest) -> APIResponse:
    """Create a new order"""
    try:
        # In a real implementation, this would:
        # 1. Validate user exists
        # 2. Validate all products exist
        # 3. Create order in database
        # 4. Create order items
        # 5. Return the created order
        
        # For mock purposes, we'll simulate this
        if not order_request.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")
        
        # Generate mock order ID
        new_order_id = max([o.order_id for o in mock_data.orders], default=0) + 1
        
        # Validate products exist
        for item in order_request.items:
            product_id = item.get("product_id")
            if not product_id or not mock_data.get_product(product_id):
                raise HTTPException(status_code=400, detail=f"Product {product_id} not found")
        
        # Create mock order response
        mock_order = {
            "order_id": new_order_id,
            "user_id": order_request.user_id,
            "eval_set": "new",
            "order_number": 1,  # Would calculate based on user's order history
            "order_dow": 1,     # Monday
            "order_hour_of_day": 14,  # 2 PM
            "days_since_prior_order": None,
            "items": [],
            "total_items": len(order_request.items),
            "status": "created"
        }
        
        # Add items with product details
        for i, item in enumerate(order_request.items):
            product = mock_data.get_product(item["product_id"])
            mock_order["items"].append({
                "order_id": new_order_id,
                "product_id": item["product_id"],
                "add_to_cart_order": i + 1,
                "reordered": 0,  # New item
                "product_name": product.product_name if product else f"Product {item['product_id']}",
                "quantity": item.get("quantity", 1)
            })
        
        return APIResponse(
            message="Order created successfully",
            data=mock_order
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/items", response_model=APIResponse)
async def add_order_items(order_id: int, items: List[dict]) -> APIResponse:
    """Add items to an existing order"""
    try:
        # Verify order exists
        order = mock_data.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if not items:
            raise HTTPException(status_code=400, detail="Must provide at least one item")
        
        # Validate products exist
        for item in items:
            product_id = item.get("product_id")
            if not product_id or not mock_data.get_product(product_id):
                raise HTTPException(status_code=400, detail=f"Product {product_id} not found")
        
        # Get current items to determine next add_to_cart_order
        current_items = mock_data.get_order_items(order_id)
        next_cart_order = len(current_items) + 1
        
        # Create mock response for added items
        added_items = []
        for item in items:
            product = mock_data.get_product(item["product_id"])
            added_items.append({
                "order_id": order_id,
                "product_id": item["product_id"],
                "add_to_cart_order": next_cart_order,
                "reordered": 0,
                "product_name": product.product_name if product else f"Product {item['product_id']}",
                "quantity": item.get("quantity", 1)
            })
            next_cart_order += 1
        
        return APIResponse(
            message=f"Added {len(added_items)} items to order {order_id}",
            data={
                "order_id": order_id,
                "added_items": added_items,
                "total_added": len(added_items)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
