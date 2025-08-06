# app/carts_routers.py

from fastapi import APIRouter, Query, HTTPException, status, Body, Path, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from .db_core.database import SessionLocal
from .db_core.models import Cart, CartItem, Product, Department, Aisle, User
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Generic, TypeVar
import datetime
from datetime import UTC

router = APIRouter(prefix="/carts", tags=["carts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Generic response model
T = TypeVar('T')

class ServiceResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] = []
    error: Optional[str] = None
    message: Optional[str] = None

class CartItemData(BaseModel):
    """Cart item model for API responses"""
    model_config = ConfigDict(from_attributes=True)
    
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

class CartData(BaseModel):
    """Cart response model"""
    model_config = ConfigDict(from_attributes=True)
    
    cart_id: str
    user_id: str
    items: List[CartItemData] = []
    total_items: int
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

class AddCartItemRequest(BaseModel):
    """Add item to cart request"""
    product_id: int
    quantity: int = 1
    add_to_cart_order: Optional[int] = 0
    reordered: int = 0

class UpdateCartItemRequest(BaseModel):
    """Update cart item request"""
    quantity: int

class CreateCartRequest(BaseModel):
    """Create cart request"""
    user_id: str
    items: List[AddCartItemRequest] = []

class UpdateCartRequest(BaseModel):
    """Update entire cart request"""
    items: List[AddCartItemRequest] = []

def verify_user_exists(session: Session, user_id: str) -> User:
    """Verify user exists and return User object"""
    try:
        # Convert string to integer
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
    
    user = session.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found")
    return user

def verify_products_exist(session: Session, product_ids: List[int]):
    """Verify all products exist"""
    existing_ids = {p.product_id for p in session.query(Product).filter(Product.product_id.in_(product_ids)).all()}
    missing_ids = [pid for pid in product_ids if pid not in existing_ids]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"Products not found: {', '.join(map(str, missing_ids))}")

def build_cart_response(session: Session, cart: Cart) -> CartData:
    """Build enriched cart response with product details"""
    cart_items = []
    
    if cart.cart_items:
        # Get all product IDs from cart items
        product_ids = [item.product_id for item in cart.cart_items]
        
        # Fetch products with enriched data
        products = (
            session.query(Product)
            .filter(Product.product_id.in_(product_ids))
            .options(
                joinedload(Product.enriched),
                joinedload(Product.aisle),
                joinedload(Product.department)
            )
            .all()
        )
        products_map = {p.product_id: p for p in products}
        
        # Build cart items with enriched data
        for cart_item in cart.cart_items:
            if cart_item.quantity > 0:
                product = products_map.get(cart_item.product_id)
                enriched = product.enriched if product else None
                
                item_data = CartItemData(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    add_to_cart_order=cart_item.add_to_cart_order,
                    reordered=cart_item.reordered,
                    product_name=product.product_name if product else None,
                    aisle_name=product.aisle.aisle if product and product.aisle else None,
                    department_name=product.department.department if product and product.department else None,
                    description=enriched.description if enriched else None,
                    price=enriched.price if enriched else None,
                    image_url=enriched.image_url if enriched else None
                )
                cart_items.append(item_data)
    
    return CartData(
        cart_id=str(cart.id),
        user_id=str(cart.user.id),
        items=cart_items,
        total_items=len(cart_items),
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )

@router.get("/{user_id}", response_model=ServiceResponse[CartData])
def get_user_cart(user_id: str, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """
    Get cart for external_user_id. If no cart exists, return an empty cart.
    """
    try:
        # Verify user exists
        user = verify_user_exists(session, user_id)
        
        # Get user's cart (use internal user ID for FK lookup)
        cart = (
            session.query(Cart)
            .filter(Cart.user_id == user.id)
            .options(joinedload(Cart.cart_items), joinedload(Cart.user))
            .first()
        )
        
        if not cart:
            # Return empty cart response
            return ServiceResponse[CartData](
                success=True,
                message=f"No cart found for user {user_id}",
                data=[]
            )
        
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Cart retrieved successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error fetching cart: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error fetching cart: {str(e)}",
            data=[]
        )

@router.post("/", response_model=ServiceResponse[CartData], status_code=201)
def create_cart(cart_request: CreateCartRequest, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """
    Create a new cart for a user.
    """
    try:
        # Verify user exists
        user = verify_user_exists(session, cart_request.user_id)
        
        # Check if cart already exists for user
        existing_cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if existing_cart:
            return ServiceResponse[CartData](
                success=False,
                error="Cart already exists for user",
                data=[]
            )
        
        # Validate products if items provided
        if cart_request.items:
            product_ids = [item.product_id for item in cart_request.items]
            verify_products_exist(session, product_ids)
        
        # Create new cart
        cart = Cart(
            user_id=user.id,  # Use internal user ID for FK
            total_items=len(cart_request.items)
        )
        session.add(cart)
        session.flush()  # Get the auto-generated cart ID
        
        # Add cart items if provided
        if cart_request.items:
            cart_items = []
            for i, item in enumerate(cart_request.items):
                cart_item = CartItem(
                    cart_id=cart.id,  # Use internal cart ID for FK
                    product_id=item.product_id,
                    quantity=item.quantity,
                    add_to_cart_order=item.add_to_cart_order or (i + 1),
                    reordered=item.reordered
                )
                cart_items.append(cart_item)
            
            session.add_all(cart_items)
        
        session.commit()
        session.refresh(cart)
        
        # Build response with enriched data
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Cart created successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error creating cart: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error creating cart: {str(e)}",
            data=[]
        )

@router.put("/{user_id}", response_model=ServiceResponse[CartData])
def update_user_cart(user_id: str, cart_request: UpdateCartRequest, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """
    Replace the entire cart for a user.
    """
    try:
        # Verify user exists
        user = verify_user_exists(session, user_id)
        
        # Validate products if items provided
        if cart_request.items:
            product_ids = [item.product_id for item in cart_request.items]
            verify_products_exist(session, product_ids)
        
        # Get or create cart
        cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            cart = Cart(user_id=user.id, total_items=0)
            session.add(cart)
            session.flush()
        
        # Remove all existing cart items
        session.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        
        # Add new cart items
        if cart_request.items:
            cart_items = []
            for i, item in enumerate(cart_request.items):
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    add_to_cart_order=item.add_to_cart_order or (i + 1),
                    reordered=item.reordered
                )
                cart_items.append(cart_item)
            
            session.add_all(cart_items)
        
        # Update cart total
        cart.total_items = len(cart_request.items)
        cart.updated_at = datetime.datetime.now(UTC)
        
        session.commit()
        session.refresh(cart)
        
        # Build response with enriched data
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Cart updated successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error updating cart: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error updating cart: {str(e)}",
            data=[]
        )

@router.delete("/{user_id}", response_model=ServiceResponse[Dict[str, Any]])
def delete_cart(user_id: str, session: Session = Depends(get_db)) -> ServiceResponse[Dict[str, Any]]:
    """
    Delete a user's cart.
    """
    try:
        # Verify user exists
        user = verify_user_exists(session, user_id)
        
        # Find and delete cart
        cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return ServiceResponse[Dict[str, Any]](
                success=False,
                error="Cart not found",
                data=[]
            )
        
        session.delete(cart)
        session.commit()
        
        return ServiceResponse[Dict[str, Any]](
            success=True,
            message="Cart deleted successfully",
            data=[{"user_id": user_id, "deleted": True}]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[Dict[str, Any]](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error deleting cart: {e}")
        return ServiceResponse[Dict[str, Any]](
            success=False,
            error=f"Error deleting cart: {str(e)}",
            data=[]
        )

@router.post("/{user_id}/items", response_model=ServiceResponse[CartData])
def add_cart_item(user_id: str, item_request: AddCartItemRequest, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """Add an item to user's cart, or increment if exists."""
    try:
        # Verify user and product
        user = verify_user_exists(session, user_id)
        verify_products_exist(session, [item_request.product_id])
        
        # Get or create cart
        cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            cart = Cart(user_id=user.id, total_items=0)
            session.add(cart)
            session.flush()
        
        # Check if item already exists in cart
        existing_item = session.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_request.product_id
        ).first()
        
        if existing_item:
            # Update existing item quantity
            existing_item.quantity += item_request.quantity
        else:
            # Add new item
            current_count = session.query(CartItem).filter(CartItem.cart_id == cart.id).count()
            new_item = CartItem(
                cart_id=cart.id,
                product_id=item_request.product_id,
                quantity=item_request.quantity,
                add_to_cart_order=item_request.add_to_cart_order or (current_count + 1),
                reordered=item_request.reordered
            )
            session.add(new_item)
        
        # Update cart total
        cart.total_items = session.query(CartItem).filter(CartItem.cart_id == cart.id).count()
        cart.updated_at = datetime.datetime.now(UTC)
        
        session.commit()
        session.refresh(cart)
        
        # Build response with enriched data
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Item added to cart successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error adding cart item: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error adding cart item: {str(e)}",
            data=[]
        )

@router.put("/{user_id}/items/{product_id}", response_model=ServiceResponse[CartData])
def update_cart_item(user_id: str, product_id: int, update_request: UpdateCartItemRequest, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """Update quantity of a specific item in cart"""
    try:
        # Verify user and product
        user = verify_user_exists(session, user_id)
        verify_products_exist(session, [product_id])
        
        # Get cart
        cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return ServiceResponse[CartData](
                success=False,
                error="Cart not found",
                data=[]
            )
        
        # Find cart item
        cart_item = session.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        ).first()
        
        if not cart_item:
            return ServiceResponse[CartData](
                success=False,
                error=f"Product {product_id} not found in cart",
                data=[]
            )
        
        if update_request.quantity <= 0:
            # Remove item from cart
            session.delete(cart_item)
        else:
            # Update quantity
            cart_item.quantity = update_request.quantity
        
        # Update cart total and timestamp
        cart.total_items = session.query(CartItem).filter(CartItem.cart_id == cart.id).count()
        cart.updated_at = datetime.datetime.now(UTC)
        
        session.commit()
        session.refresh(cart)
        
        # Build response with enriched data
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Cart item updated successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error updating cart item: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error updating cart item: {str(e)}",
            data=[]
        )

@router.delete("/{user_id}/items/{product_id}", response_model=ServiceResponse[CartData])
def remove_cart_item(user_id: str, product_id: int, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """Remove a specific item from cart"""
    try:
        # Verify user exists
        user = verify_user_exists(session, user_id)
        
        # Get cart
        cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return ServiceResponse[CartData](
                success=False,
                error="Cart not found",
                data=[]
            )
        
        # Find and remove cart item
        cart_item = session.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        ).first()
        
        if not cart_item:
            return ServiceResponse[CartData](
                success=False,
                error=f"Product {product_id} not found in cart",
                data=[]
            )
        
        session.delete(cart_item)
        
        # Update cart total and timestamp
        cart.total_items = session.query(CartItem).filter(CartItem.cart_id == cart.id).count()
        cart.updated_at = datetime.datetime.now(UTC)
        
        session.commit()
        session.refresh(cart)
        
        # Build response with enriched data
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Item removed from cart successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error removing cart item: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error removing cart item: {str(e)}",
            data=[]
        )

@router.delete("/{user_id}/clear", response_model=ServiceResponse[CartData])
def clear_user_cart(user_id: str, session: Session = Depends(get_db)) -> ServiceResponse[CartData]:
    """Clear all items from cart for a user"""
    try:
        # Verify user exists
        user = verify_user_exists(session, user_id)
        
        # Get cart
        cart = session.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return ServiceResponse[CartData](
                success=False,
                error="Cart not found",
                data=[]
            )
        
        # Remove all cart items
        session.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        
        # Update cart
        cart.total_items = 0
        cart.updated_at = datetime.datetime.now(UTC)
        
        session.commit()
        session.refresh(cart)
        
        # Build response with enriched data
        cart_data = build_cart_response(session, cart)
        
        return ServiceResponse[CartData](
            success=True,
            message="Cart cleared successfully",
            data=[cart_data]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[CartData](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error clearing cart: {e}")
        return ServiceResponse[CartData](
            success=False,
            error=f"Error clearing cart: {str(e)}",
            data=[]
        )

@router.post("/{user_id}/checkout", response_model=ServiceResponse[Dict[str, Any]])
def checkout_cart(user_id: str, session: Session = Depends(get_db)) -> ServiceResponse[Dict[str, Any]]:
    """Convert cart to order (checkout process)"""
    try:
        # Verify user exists
        user = verify_user_exists(session, user_id)
        
        # Get cart with items
        cart = (
            session.query(Cart)
            .filter(Cart.user_id == user.id)
            .options(joinedload(Cart.cart_items))
            .first()
        )
        
        if not cart or not cart.cart_items:
            return ServiceResponse[Dict[str, Any]](
                success=False,
                error="Cart is empty",
                data=[]
            )
        
        # TODO: Implement actual order creation
        # For now, simulate checkout and clear cart
        
        # Clear cart items
        session.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        cart.total_items = 0
        cart.updated_at = datetime.datetime.now(UTC)
        
        session.commit()
        
        return ServiceResponse[Dict[str, Any]](
            success=True,
            message="Checkout completed successfully",
            data=[{
                "user_id": user_id,
                "status": "checkout_completed",
                "note": "Cart cleared - order creation would be implemented here"
            }]
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        return ServiceResponse[Dict[str, Any]](
            success=False,
            error="Database error occurred",
            data=[]
        )
    except Exception as e:
        session.rollback()
        print(f"Error at checkout: {e}")
        return ServiceResponse[Dict[str, Any]](
            success=False,
            error=f"Error at checkout: {str(e)}",
            data=[]
        )
