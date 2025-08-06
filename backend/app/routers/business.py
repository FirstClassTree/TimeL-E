# backend/app/routers/business.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from ..models.base import APIResponse, Cart, CartItem, Order
from ..services.http_client import db_service, ml_service
import asyncio

router = APIRouter(prefix="", tags=["Business Logic"])

# Cart Management Endpoints

@router.post("/carts/{user_id}/items")
async def add_cart_item(user_id: str, item: CartItem) -> APIResponse:
    """Add item to user's cart"""
    try:
        # Get current cart or create new one
        try:
            cart_data = await db_service.get_entity("carts", user_id)
            cart = Cart(**cart_data)
        except:
            # Create new cart if doesn't exist
            cart = Cart(user_id=user_id, items=[])
        
        # Add or update item in cart
        item_found = False
        for existing_item in cart.items:
            if existing_item.item_id == item.item_id:
                existing_item.quantity += item.quantity
                item_found = True
                break
        
        if not item_found:
            cart.items.append(item)
        
        # Save updated cart
        result = await db_service.update_entity("carts", user_id, cart.model_dump(by_alias=True))
        
        return APIResponse(
            message="Item added to cart successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/carts/{user_id}")
async def get_user_cart(user_id: str) -> APIResponse:
    """Get user's current cart"""
    try:
        cart_data = await db_service.get_entity("carts", user_id)
        return APIResponse(
            message="Cart retrieved successfully",
            data=cart_data
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Cart not found for user {user_id}")

@router.put("/carts/{user_id}")
async def update_user_cart(user_id: str, cart: Cart) -> APIResponse:
    """Update user's entire cart"""
    try:
        cart.user_id = user_id  # Ensure user_id matches
        result = await db_service.update_entity("carts", user_id, cart.model_dump(by_alias=True))
        
        return APIResponse(
            message="Cart updated successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/carts/{user_id}/items/{item_id}")
async def remove_cart_item(user_id: str, item_id: str) -> APIResponse:
    """Remove specific item from user's cart"""
    try:
        # Get current cart
        cart_data = await db_service.get_entity("carts", user_id)
        cart = Cart(**cart_data)
        
        # Remove item
        cart.items = [item for item in cart.items if item.item_id != item_id]
        
        # Save updated cart
        result = await db_service.update_entity("carts", user_id, cart.model_dump(by_alias=True))
        
        return APIResponse(
            message="Item removed from cart successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Order Management Endpoints

@router.post("/orders")
async def create_order(order: Order) -> APIResponse:
    """Create new order"""
    try:
        # Validate cart exists
        cart_data = await db_service.get_entity("carts", order.user_id)
        
        # If no items provided, use cart items
        if not order.items:
            cart = Cart(**cart_data)
            order.items = cart.items
        
        # Create order in database
        result = await db_service.create_entity("orders", order.model_dump(by_alias=True))
        
        return APIResponse(
            message="Order created successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{user_id}")
async def get_user_orders(user_id: str) -> APIResponse:
    """Get user's order history"""
    try:
        result = await db_service.list_entities("orders", {"user_id": user_id})
        
        return APIResponse(
            message="Orders retrieved successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ML Integration Endpoints

@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str) -> APIResponse:
    """Get ML recommendations for user"""
    try:
        # Get user's cart and order history for context
        cart_task = db_service.get_entity("carts", user_id)
        orders_task = db_service.list_entities("orders", {"user_id": user_id})
        
        # Execute both requests concurrently
        cart_data, orders_data = await asyncio.gather(
            cart_task, orders_task, return_exceptions=True
        )
        
        # Prepare context for ML service
        context = {
            "current_cart": cart_data if not isinstance(cart_data, Exception) else None,
            "order_history": orders_data if not isinstance(orders_data, Exception) else None
        }
        
        # Get recommendations from ML service
        recommendations = await ml_service.get_recommendations(user_id, context)
        
        return APIResponse(
            message="Recommendations retrieved successfully",
            data=recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/carts/{user_id}/smart-suggestions")
async def get_smart_cart_suggestions(user_id: str, current_cart: Cart) -> APIResponse:
    """Get intelligent cart suggestions based on current cart and ML predictions"""
    try:
        # Get ML predictions for this user and cart context
        prediction_data = {
            "user_id": user_id,
            "current_cart": current_cart.model_dump(by_alias=True),
            "action": "suggest_additions"
        }
        
        suggestions = await ml_service.predict(prediction_data)
        
        return APIResponse(
            message="Smart cart suggestions generated successfully",
            data=suggestions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
