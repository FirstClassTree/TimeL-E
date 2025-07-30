# backend/app/routers/cart.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from ..models.base import APIResponse
from ..services.database_service import db_service

router = APIRouter(prefix="/cart", tags=["Cart"])

class CartItem(BaseModel):
    """Cart item model"""
    product_id: int
    quantity: int = 1
    product_name: Optional[str] = None
    aisle_name: Optional[str] = None
    department_name: Optional[str] = None

class CartResponse(BaseModel):
    """Cart response model"""
    user_id: str
    items: List[CartItem]
    total_items: int
    total_quantity: int

class AddCartItemRequest(BaseModel):
    """Add item to cart request"""
    product_id: int
    quantity: int = 1

class UpdateCartItemRequest(BaseModel):
    """Update cart item request"""
    quantity: int

# In-memory cart storage (replace with database in production)
# Format: {user_id: {product_id: quantity}}
cart_storage = {}

@router.get("/{user_id}", response_model=APIResponse)
async def get_user_cart(user_id: str) -> APIResponse:
    """Get cart for a specific user"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get cart from storage
        user_cart = cart_storage.get(user_id, {})
        
        if not user_cart:
            return APIResponse(
                message=f"Cart is empty for user {user_id}",
                data=CartResponse(
                    user_id=user_id,
                    items=[],
                    total_items=0,
                    total_quantity=0
                )
            )
        
        # Enrich cart items with product details
        cart_items = []
        total_quantity = 0
        
        for product_id, quantity in user_cart.items():
            # Get product details
            product_result = await db_service.get_product_by_id(int(product_id))
            
            if product_result.get("success", True) and product_result.get("data", []):
                product = product_result["data"][0]
                cart_item = CartItem(
                    product_id=product["product_id"],
                    quantity=quantity,
                    product_name=product["product_name"],
                    aisle_name=product.get("aisle_name"),
                    department_name=product.get("department_name")
                )
                cart_items.append(cart_item)
                total_quantity += quantity
            else:
                # Product not found, remove from cart
                cart_storage[user_id].pop(str(product_id), None)
        
        cart_response = CartResponse(
            user_id=user_id,
            items=cart_items,
            total_items=len(cart_items),
            total_quantity=total_quantity
        )
        
        return APIResponse(
            message=f"Cart retrieved successfully for user {user_id}",
            data=cart_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}", response_model=APIResponse)
async def update_user_cart(user_id: str, cart_items: List[AddCartItemRequest]) -> APIResponse:
    """Replace entire cart for a user"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Validate all products exist
        for item in cart_items:
            product_result = await db_service.get_product_by_id(item.product_id)
            if not product_result.get("success", True) or not product_result.get("data", []):
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        # Replace cart in storage
        new_cart = {}
        for item in cart_items:
            if item.quantity > 0:  # Only add items with positive quantity
                new_cart[str(item.product_id)] = item.quantity
        
        cart_storage[user_id] = new_cart
        
        # Return updated cart
        return await get_user_cart(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/items", response_model=APIResponse)
async def add_cart_item(user_id: str, item_request: AddCartItemRequest) -> APIResponse:
    """Add an item to user's cart"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Verify product exists
        product_result = await db_service.get_product_by_id(item_request.product_id)
        if not product_result.get("success", True) or not product_result.get("data", []):
            raise HTTPException(status_code=400, detail=f"Product {item_request.product_id} not found")
        
        # Initialize cart if doesn't exist
        if user_id not in cart_storage:
            cart_storage[user_id] = {}
        
        # Add or update item in cart
        product_key = str(item_request.product_id)
        current_quantity = cart_storage[user_id].get(product_key, 0)
        new_quantity = current_quantity + item_request.quantity
        
        if new_quantity <= 0:
            # Remove item if quantity becomes 0 or negative
            cart_storage[user_id].pop(product_key, None)
        else:
            cart_storage[user_id][product_key] = new_quantity
        
        product = product_result["data"][0]
        
        return APIResponse(
            message=f"Item {product['product_name']} added to cart",
            data={
                "user_id": user_id,
                "product_id": item_request.product_id,
                "product_name": product["product_name"],
                "previous_quantity": current_quantity,
                "added_quantity": item_request.quantity,
                "new_quantity": new_quantity if new_quantity > 0 else 0
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/items/{product_id}", response_model=APIResponse)
async def update_cart_item(user_id: str, product_id: int, update_request: UpdateCartItemRequest) -> APIResponse:
    """Update quantity of a specific item in cart"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Verify product exists
        product_result = await db_service.get_product_by_id(product_id)
        if not product_result.get("success", True) or not product_result.get("data", []):
            raise HTTPException(status_code=400, detail=f"Product {product_id} not found")
        
        # Check if user has cart and item
        if user_id not in cart_storage or str(product_id) not in cart_storage[user_id]:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found in cart")
        
        product_key = str(product_id)
        
        if update_request.quantity <= 0:
            # Remove item from cart
            cart_storage[user_id].pop(product_key, None)
            message = f"Product {product_id} removed from cart"
            new_quantity = 0
        else:
            # Update quantity
            cart_storage[user_id][product_key] = update_request.quantity
            message = f"Product {product_id} quantity updated"
            new_quantity = update_request.quantity
        
        product = product_result["data"][0]
        
        return APIResponse(
            message=message,
            data={
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product["product_name"],
                "new_quantity": new_quantity
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/items/{product_id}", response_model=APIResponse)
async def remove_cart_item(user_id: str, product_id: int) -> APIResponse:
    """Remove a specific item from cart"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Check if user has cart and item
        if user_id not in cart_storage or str(product_id) not in cart_storage[user_id]:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found in cart")
        
        # Get product name for response
        product_result = await db_service.get_product_by_id(product_id)
        product_name = "Unknown Product"
        if product_result.get("success", True) and product_result.get("data", []):
            product_name = product_result["data"][0]["product_name"]
        
        # Remove item from cart
        removed_quantity = cart_storage[user_id].pop(str(product_id), 0)
        
        return APIResponse(
            message=f"Product {product_name} removed from cart",
            data={
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product_name,
                "removed_quantity": removed_quantity
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}", response_model=APIResponse)
async def clear_user_cart(user_id: str) -> APIResponse:
    """Clear entire cart for a user"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Clear cart
        items_count = len(cart_storage.get(user_id, {}))
        cart_storage[user_id] = {}
        
        return APIResponse(
            message=f"Cart cleared for user {user_id}",
            data={
                "user_id": user_id,
                "cleared_items": items_count,
                "cart_empty": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/checkout", response_model=APIResponse)
async def checkout_cart(user_id: str) -> APIResponse:
    """Convert cart to order (checkout process)"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get current cart
        user_cart = cart_storage.get(user_id, {})
        
        if not user_cart:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Prepare order items from cart
        order_items = []
        for product_id, quantity in user_cart.items():
            order_items.append({
                "product_id": int(product_id),
                "quantity": quantity
            })
        
        # TODO: Create actual order using the order creation endpoint
        # For now, simulate the checkout process
        
        # Clear cart after checkout
        cart_storage[user_id] = {}
        
        return APIResponse(
            message=f"Checkout completed for user {user_id}",
            data={
                "user_id": user_id,
                "order_items": order_items,
                "total_items": len(order_items),
                "status": "order_created",
                "note": "This is a simulation - actual order creation would be implemented here"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
