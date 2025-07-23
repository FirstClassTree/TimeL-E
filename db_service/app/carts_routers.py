# app/carts_routers.py

from fastapi import APIRouter, Query, HTTPException, status, Body, Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.db_core.database import SessionLocal
import asyncpg
from app.db_core.models import Order, OrderItem, OrderStatus, Product, Department, Aisle, User
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
# Removed UUID imports since we're using integer user_ids and order_ids
import datetime

router = APIRouter(prefix="/carts", tags=["carts"])

class CartItem(BaseModel):
    """Cart item model"""
    product_id: int
    quantity: int = 1
    product_name: Optional[str] = None
    aisle_name: Optional[str] = None
    department_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None

class Cart(BaseModel):
    user_id: int
    items: List[CartItem] = []
    updated_at: Optional[datetime.datetime] = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    metadata: Optional[Dict[str, Any]] = None

class CartResponse(BaseModel):
    """Cart response model"""
    user_id: int
    items: List[CartItem]
    total_items: int
    total_quantity: int
    updated_at: Optional[datetime.datetime] = None

class AddCartItemRequest(BaseModel):
    """Add item to cart request"""
    product_id: int
    quantity: int = 1

class UpdateCartItemRequest(BaseModel):
    """Update cart item request"""
    quantity: int

class CreateCartRequest(BaseModel):
    user_id: int
    items: List[CartItem]

class UpdateCartRequest(BaseModel):
    items: List[CartItem]

# ====================
# MOCKED IN-MEMORY STORE FOR DEMO PURPOSES
carts_db: Dict[int, Cart] = {}


# Helper function to verify user existence
def verify_user_exists(session: Session, user_id: int):
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user

# Helper function to verify all products exist
def verify_all_products_exist(session: Session, product_ids: List[int]):
    existing_ids = {p.product_id for p in session.query(Product).filter(Product.product_id.in_(product_ids)).all()}
    for pid in product_ids:
        if pid not in existing_ids:
            raise HTTPException(status_code=400, detail=f"Product {pid} not found")

def build_cart_response(session: Session, user_id: int, cart: Cart) -> CartResponse:
    """
    Given a Cart object, enrich items and return CartResponse.
    """
    cart_items = []
    total_quantity = 0
    product_ids = [item.product_id for item in cart.items]
    if not product_ids:
        return CartResponse(
            user_id=user_id,
            items=[],
            total_items=0,
            total_quantity=0,
            updated_at=getattr(cart, "updated_at", None)
        )
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
    for item in cart.items:
        if item.quantity > 0:
            p = products_map.get(item.product_id)
            enriched = p.enriched if p else None
            cart_item = CartItem(
                product_id=item.product_id,
                quantity=item.quantity,
                product_name=p.product_name if p else None,
                aisle_name=p.aisle.aisle_name if p and p.aisle else None,
                department_name=p.department.department_name if p and p.department else None,
                description=enriched.description if enriched else None,
                price=enriched.price if enriched else None,
                image_url=enriched.image_url if enriched else None
            )
            cart_items.append(cart_item)
            total_quantity += item.quantity
    return CartResponse(
        user_id=user_id,
        items=cart_items,
        total_items=len(cart_items),
        total_quantity=total_quantity
    )

def get_enriched_product_info(session: Session, product_id: int):
    # Query the main Product and join the related tables
    product = (
        session.query(Product)
        .options(
            joinedload(Product.enriched),
            joinedload(Product.aisle),
            joinedload(Product.department)
        )
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        return None

    # Compose the dict for API response
    enriched = product.enriched  # ProductEnriched object or None
    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "aisle_name": product.aisle.aisle_name if product.aisle else None,
        "department_name": product.department.department_name if product.department else None,
        "description": enriched.description if enriched else None,
        "price": enriched.price if enriched else None,
        "image_url": enriched.image_url if enriched else None,
    }

# GET /carts/{user_id}
@router.get("/{user_id}", response_model=CartResponse)
def get_user_cart(user_id: int):
    """
    Get cart for user_id.
    """
    session = SessionLocal()
    try:
        # --- User Validation ---
        verify_user_exists(session, user_id)

        # TODO: Fetch cart for user_id. empty if not found.
        # TODO: Actually fetch from DB, or create new empty cart

        # --- Cart Fetch (mocked) ---
        cart = carts_db.get(user_id)    # TODO: read from DB
        if not cart:
            cart = Cart(user_id=user_id, items=[])

        # # auto-create an empty cart
        # if not cart:
        #     cart = Cart(user_id=user_id, items=[])
        #     carts_db[user_id] = cart        # TODO: insert into DB
        #     cart = carts_db.get(user_id)    # TODO: read from DB

        # # error when cart does not exist
        # if cart is None:
        #     raise HTTPException(status_code=404, detail=f"Cart for user {user_id} not found")

        return build_cart_response(session, user_id, cart)

    except Exception as e:
        print(f"Error fetching cart: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cart")
    finally:
        session.close()

@router.put("/{user_id}", response_model=CartResponse)
def update_user_cart(user_id: int, cart: Cart):
    """
    Replace the entire cart for a user.
    If cart does not exist, creates new.
    Validates user and all products.
    """
    session = SessionLocal()
    try:
        # --- Validate user ---
        verify_user_exists(session, user_id)

        # --- Validate all products ---
        product_ids = [item.product_id for item in cart.items]
        if product_ids:
            verify_all_products_exist(session, product_ids)

        # --- Replace (or create) cart ---
        cart.user_id = user_id  # ensure consistency
        cart.updated_at = datetime.datetime.now(datetime.UTC)
        carts_db[user_id] = cart  # TODO: Replace with DB upsert

        # --------- CRUCIAL: Re-read latest cart state -----------
        # In production: Fetch the cart and all related items from DB, not from input
        # In mock, just read from the carts_db dict for consistency:
        saved_cart = carts_db.get(user_id)  # TODO: Fetch the cart and all related items from DB
        if not saved_cart:
            raise HTTPException(status_code=500, detail="Failed to persist cart")

        # --- Build enriched response ---
        return build_cart_response(session, saved_cart.user_id, saved_cart)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating cart: {e}")
        raise HTTPException(status_code=500, detail="Error updating cart")
    finally:
        session.close()

# POST /carts/
@router.post("/", response_model=CartResponse, status_code=201)
def create_cart(cart: Cart):
    """
    Create a new cart for a user.
    - Fails if a cart already exists for the user.
    - Validates user existence and all products.
    - Returns the full, enriched cart.
    """
    session = SessionLocal()
    try:
        # --- Validate user existence ---
        verify_user_exists(session, cart.user_id)

        # --- Validate all product IDs ---
        product_ids = [item.product_id for item in cart.items]
        if product_ids:
            verify_all_products_exist(session, product_ids)

        # --- Fail if cart already exists ---
        if cart.user_id in carts_db:    # TODO: check in DB
            raise HTTPException(status_code=409, detail="Cart already exists for user")

        # --- Set updated_at ---
        cart.updated_at = datetime.datetime.now(datetime.UTC)

        # --- Save to (mock) DB ---
        carts_db[cart.user_id] = cart  # TODO: replace with real DB insert

        # --------- CRUCIAL: Re-read latest cart state -----------
        # In production: Fetch the cart and all related items from DB, not from input
        # In mock, just read from the carts_db dict for consistency:
        saved_cart = carts_db.get(cart.user_id)  # TODO: Fetch the cart and all related items from DB
        if not saved_cart:
            raise HTTPException(status_code=500, detail="Failed to persist cart")

        # --- Return enriched response ---
        return build_cart_response(session, saved_cart.user_id, saved_cart)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating cart: {e}")
        raise HTTPException(status_code=500, detail="Error creating cart")
    finally:
        session.close()

# DELETE /carts/{user_id}
@router.delete("/{user_id}", status_code=200)
def delete_cart(user_id: int):
    """
    Delete a user's cart.
    - 404 if user does not exist or cart not found.
    """
    session = SessionLocal()
    try:
        # --- Validate user existence ---
        verify_user_exists(session, user_id)

        # --- Delete from (mock) DB ---
        if user_id in carts_db: # TODO: check in realDB
            del carts_db[user_id]  # TODO: Remove from real DB
            return {"message": f"Cart deleted successfully for user {user_id}"}
        else:
            raise HTTPException(status_code=404, detail="Cart not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting cart: {e}")
        raise HTTPException(status_code=500, detail="Error deleting cart")
    finally:
        session.close()

