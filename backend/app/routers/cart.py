# backend/app/routers/cart.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, NoReturn
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from ..models.base import APIResponse
from ..services.database_service import db_service

router = APIRouter(prefix="/cart", tags=["Cart"])

class CartItem(BaseModel):
    """Cart item model"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    product_id: int
    quantity: int = 1
    add_to_cart_order: int = 0
    reordered: int = 0
    product_name: Optional[str] = None
    aisle_name: Optional[str] = None
    department_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None

class CartResponse(BaseModel):
    """Cart response model"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    cart_id: str
    user_id: str
    items: List[CartItem]
    total_items: int

class AddCartItemRequest(BaseModel):
    """Add item to cart request"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    product_id: int
    quantity: int = 1
    add_to_cart_order: Optional[int] = 0
    reordered: int = 0

class UpdateCartItemRequest(BaseModel):
    """Update cart item request"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    quantity: int

class CreateCartRequest(BaseModel):
    """Create cart request"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    user_id: str
    items: List[AddCartItemRequest] = []

class UpdateCartRequest(BaseModel):
    """Update entire cart request"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    items: List[AddCartItemRequest] = []

def _handle_db_service_error(result: dict, entity_id: Optional[str] = None, operation: str = "operation",
                             default_error: str = "Operation failed"):
    """
    Centralized handler for db_service errors.
    Raises HTTPException with appropriate status code and detail message.
    """
    if not result.get("success", False):
        error_msg = result.get("error", default_error).lower()
        print(f"db_service {operation} failed with error: {error_msg}")

        status_code = 500
        detail = f"An internal server error occurred during {operation}."

        if "user not found" in error_msg:
            status_code = 404
            detail = f"User {entity_id} not found" if entity_id else "User not found"
        elif "cart not found" in error_msg:
            status_code = 404
            detail = f"Cart not found for user {entity_id}" if entity_id else "Cart not found"
        elif "product" in error_msg and "not found" in error_msg:
            status_code = 400
            detail = "One or more products not found"
        elif "cart already exists" in error_msg:
            status_code = 409
            detail = "Cart already exists for user"
        elif "cart is empty" in error_msg:
            status_code = 400
            detail = "Cart is empty"
        elif "database error" in error_msg:
            status_code = 503
            detail = "Service temporarily unavailable"
        else:
            # Fallback for other db_service errors
            detail = f"{operation.capitalize()} failed"

        raise HTTPException(status_code=status_code, detail=detail, headers={"X-Handled-Error": "true"})

def _handle_unhandled_http_exception(e: HTTPException, operation_error_message: str) -> NoReturn:
    """
    Helper to handle unhandled HTTPExceptions that don't have the X-Handled-Error header.
    """
    # Check if this HTTPException was handled by the centralized handler
    if e.headers and e.headers.get("X-Handled-Error") == "true":
        raise
    else:
        # Log and sanitize unknown HTTPExceptions
        print(f"Unknown HTTPException caught: {str(e)}")
        raise HTTPException(status_code=500, detail=operation_error_message)

@router.get("/{user_id}", response_model=APIResponse)
async def get_user_cart(user_id: str) -> APIResponse:
    """Get cart for a specific user"""
    try:
        # Get cart from db_service
        cart_result = await db_service.get_entity("carts", user_id)
        _handle_db_service_error(cart_result, user_id, "get cart", "Failed to get cart")
        
        cart_data = cart_result.get("data", [])
        
        if not cart_data:
            return APIResponse(
                message=f"No cart found for user {user_id}",
                data=CartResponse(
                    cart_id="",
                    user_id=user_id,
                    items=[],
                    total_items=0
                )
            )
        
        # Convert cart data to response format
        cart = cart_data[0]
        cart_items = [CartItem(**item) for item in cart.get("items", [])]
        
        cart_response = CartResponse(
            cart_id=cart["cart_id"],
            user_id=cart["user_id"],
            items=cart_items,
            total_items=cart["total_items"]
        )
        
        return APIResponse(
            message=f"Cart retrieved successfully for user {user_id}",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to get cart due to server error")
    except Exception as e:
        print(f"Get cart failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cart due to server error")

@router.post("/", response_model=APIResponse, status_code=201)
async def create_cart(cart_request: CreateCartRequest) -> APIResponse:
    """Create a new cart for a user"""
    try:
        # Create cart using db_service
        create_result = await db_service.create_entity("carts", cart_request.model_dump(exclude_unset=True))
        _handle_db_service_error(create_result, cart_request.user_id, "create cart", "Failed to create cart")
        
        cart_data = create_result.get("data", [])
        
        if not cart_data:
            raise HTTPException(status_code=500, detail="Cart creation returned no data", headers={"X-Handled-Error": "true"})
        
        # Convert cart data to response format
        cart = cart_data[0]
        cart_items = [CartItem(**item) for item in cart.get("items", [])]
        
        cart_response = CartResponse(
            cart_id=cart["cart_id"],
            user_id=cart["user_id"],
            items=cart_items,
            total_items=cart["total_items"]
        )
        
        return APIResponse(
            message="Cart created successfully",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to create cart due to server error")
    except Exception as e:
        print(f"Create cart failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create cart due to server error")

@router.put("/{user_id}", response_model=APIResponse)
async def update_user_cart(user_id: str, cart_request: UpdateCartRequest) -> APIResponse:
    """Replace entire cart for a user"""
    try:
        # Update cart using db_service
        update_result = await db_service.update_entity("carts", user_id, cart_request.model_dump(exclude_unset=True))
        _handle_db_service_error(update_result, user_id, "update cart", "Failed to update cart")
        
        cart_data = update_result.get("data", [])
        
        if not cart_data:
            raise HTTPException(status_code=404, detail=f"Cart not found for user {user_id}", headers={"X-Handled-Error": "true"})
        
        # Convert cart data to response format
        cart = cart_data[0]
        cart_items = [CartItem(**item) for item in cart.get("items", [])]
        
        cart_response = CartResponse(
            cart_id=cart["cart_id"],
            user_id=cart["user_id"],
            items=cart_items,
            total_items=cart["total_items"]
        )
        
        return APIResponse(
            message="Cart updated successfully",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to update cart due to server error")
    except Exception as e:
        print(f"Update cart failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update cart due to server error")

@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user_cart(user_id: str) -> APIResponse:
    """Delete a user's cart"""
    try:
        # Delete cart using db_service
        delete_result = await db_service.delete_entity("carts", user_id)
        _handle_db_service_error(delete_result, user_id, "delete cart", "Failed to delete cart")
        
        return APIResponse(
            message=f"Cart deleted successfully for user {user_id}",
            data={"user_id": user_id, "deleted": True}
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to delete cart due to server error")
    except Exception as e:
        print(f"Delete cart failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete cart due to server error")

@router.post("/{external_user_id}/items", response_model=APIResponse)
async def add_cart_item(external_user_id: str, item_request: AddCartItemRequest) -> APIResponse:
    """Add an item to user's cart"""
    try:
        # Add item to cart using db_service
        add_result = await db_service.create_entity(f"carts/{external_user_id}/items", item_request.model_dump(exclude_unset=True))
        _handle_db_service_error(add_result, external_user_id, "add cart item", "Failed to add item to cart")
        
        cart_data = add_result.get("data", [])
        
        if not cart_data:
            raise HTTPException(status_code=500, detail="Add cart item returned no data", headers={"X-Handled-Error": "true"})
        
        # Convert cart data to response format
        cart = cart_data[0]
        cart_items = [CartItem(**item) for item in cart.get("items", [])]
        
        cart_response = CartResponse(
            external_cart_id=cart["external_cart_id"],
            external_user_id=cart["external_user_id"],
            items=cart_items,
            total_items=cart["total_items"]
        )
        
        return APIResponse(
            message="Item added to cart successfully",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to add item to cart due to server error")
    except Exception as e:
        print(f"Add cart item failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add item to cart due to server error")

@router.put("/{external_user_id}/items/{product_id}", response_model=APIResponse)
async def update_cart_item(external_user_id: str, product_id: int, update_request: UpdateCartItemRequest) -> APIResponse:
    """Update quantity of a specific item in cart"""
    try:
        # Update cart item using db_service
        update_result = await db_service.update_entity(f"carts/{external_user_id}/items", str(product_id), update_request.model_dump(exclude_unset=True))
        _handle_db_service_error(update_result, external_user_id, "update cart item", "Failed to update cart item")
        
        cart_data = update_result.get("data", [])
        
        if not cart_data:
            raise HTTPException(status_code=404, detail=f"Cart item not found", headers={"X-Handled-Error": "true"})
        
        # Convert cart data to response format
        cart = cart_data[0]
        cart_items = [CartItem(**item) for item in cart.get("items", [])]
        
        cart_response = CartResponse(
            external_cart_id=cart["external_cart_id"],
            external_user_id=cart["external_user_id"],
            items=cart_items,
            total_items=cart["total_items"]
        )
        
        return APIResponse(
            message="Cart item updated successfully",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to update cart item due to server error")
    except Exception as e:
        print(f"Update cart item failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update cart item due to server error")

@router.delete("/{external_user_id}/items/{product_id}", response_model=APIResponse)
async def remove_cart_item(external_user_id: str, product_id: int) -> APIResponse:
    """Remove a specific item from cart"""
    try:
        # Remove cart item using db_service
        delete_result = await db_service.delete_entity(f"carts/{external_user_id}/items", str(product_id))
        _handle_db_service_error(delete_result, external_user_id, "remove cart item", "Failed to remove cart item")
        
        cart_data = delete_result.get("data", [])
        
        if not cart_data:
            raise HTTPException(status_code=404, detail=f"Cart item not found", headers={"X-Handled-Error": "true"})
        
        # Convert cart data to response format
        cart = cart_data[0]
        cart_items = [CartItem(**item) for item in cart.get("items", [])]
        
        cart_response = CartResponse(
            external_cart_id=cart["external_cart_id"],
            external_user_id=cart["external_user_id"],
            items=cart_items,
            total_items=cart["total_items"]
        )
        
        return APIResponse(
            message="Item removed from cart successfully",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to remove cart item due to server error")
    except Exception as e:
        print(f"Remove cart item failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove cart item due to server error")

@router.delete("/{external_user_id}/clear", response_model=APIResponse)
async def clear_user_cart(external_user_id: str) -> APIResponse:
    """Clear entire cart for a user"""
    try:
        # Clear cart using db_service
        clear_result = await db_service.delete_entity(f"carts/{external_user_id}", "clear")
        _handle_db_service_error(clear_result, external_user_id, "clear cart", "Failed to clear cart")
        
        cart_data = clear_result.get("data", [])
        
        if not cart_data:
            raise HTTPException(status_code=404, detail=f"Cart not found", headers={"X-Handled-Error": "true"})
        
        # Convert cart data to response format
        cart = cart_data[0]
        
        cart_response = CartResponse(
            external_cart_id=cart["external_cart_id"],
            external_user_id=cart["external_user_id"],
            items=[],
            total_items=0
        )
        
        return APIResponse(
            message=f"Cart cleared successfully for user {external_user_id}",
            data=cart_response
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to clear cart due to server error")
    except Exception as e:
        print(f"Clear cart failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cart due to server error")

@router.post("/{external_user_id}/checkout", response_model=APIResponse)
async def checkout_cart(external_user_id: str) -> APIResponse:
    """Convert cart to order (checkout process)"""
    try:
        # Checkout cart using db_service
        checkout_result = await db_service.create_entity(f"carts/{external_user_id}/checkout", {})
        _handle_db_service_error(checkout_result, external_user_id, "checkout cart", "Failed to checkout cart")
        
        checkout_data = checkout_result.get("data", [])
        
        if not checkout_data:
            raise HTTPException(status_code=500, detail="Checkout returned no data", headers={"X-Handled-Error": "true"})
        
        return APIResponse(
            message=f"Checkout completed successfully for user {external_user_id}",
            data=checkout_data[0]
        )
        
    except HTTPException as e:
        _handle_unhandled_http_exception(e, "Failed to checkout cart due to server error")
    except Exception as e:
        print(f"Checkout failed with error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to checkout cart due to server error")
