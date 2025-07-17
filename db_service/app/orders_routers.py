# app/orders_routers.py

from fastapi import APIRouter, Query, HTTPException, status, Body, Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.database import SessionLocal
import asyncpg
from app.models import Order, OrderItem, OrderStatus, Product, Department, Aisle, User
from pydantic import BaseModel
from typing import List, Optional
from uuid_utils import uuid7
# from uuid import uuid7   # native uuid7 in python 3.14
import uuid

router = APIRouter(prefix="/orders", tags=["orders"])

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int = 1

    # The order in which the item was added to the cart (useful for UI reordering, analytics, etc.)
    add_to_cart_order: int = None

    # The order in which the item was added to the cart (useful for UI reordering, analytics, etc.)
    reordered: int = 0

class CreateOrderRequest(BaseModel):
    user_id: str
    eval_set: Optional[str] = "new"
    order_dow: int = None
    order_hour_of_day: int = None
    days_since_prior_order: Optional[int] = None
    total_items: int = None
    status: Optional[str] = "pending"
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    items: List[OrderItemRequest]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order_request: CreateOrderRequest):
    session = SessionLocal()
    try:
        # Optionally validate user exists
        user = session.query(User).filter_by(user_id=order_request.user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail=f"User {order_request.user_id} not found")
        if not order_request.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")

        # Optionally validate all products exist
        product_ids = [item.product_id for item in order_request.items]
        existing_products = session.query(Product.product_id).filter(Product.product_id.in_(product_ids)).all()
        existing_product_ids = {p[0] for p in existing_products}
        missing_product_ids = [pid for pid in product_ids if pid not in existing_product_ids]
        if missing_product_ids:
            raise HTTPException(status_code=400,
                                detail=f"Products not found: {', '.join(map(str, missing_product_ids))}")

        # Create the order
        last_order = (
            session.query(Order)
            .filter_by(user_id=order_request.user_id)
            .order_by(Order.order_number.desc())
            .first()
        )
        next_order_number = (last_order.order_number if last_order else 0) + 1
        order = Order(
            user_id=order_request.user_id,
            order_id=uuid.UUID(str(uuid7())),
            eval_set=order_request.eval_set,
            order_number=next_order_number,
            order_dow=order_request.order_dow,
            order_hour_of_day=order_request.order_hour_of_day,
            days_since_prior_order=order_request.days_since_prior_order,
            total_items=len(order_request.items),
            status=OrderStatus(order_request.status) if order_request.status else OrderStatus.PENDING,
            phone_number=order_request.phone_number,
            street_address=order_request.street_address,
            city=order_request.city,
            postal_code=order_request.postal_code,
            country=order_request.country,
            tracking_number=order_request.tracking_number,
            shipping_carrier=order_request.shipping_carrier,
            tracking_url=order_request.tracking_url
        )
        session.add(order)
        # session.flush()  # To get order_id

        # Create order items
        for i, item in enumerate(order_request.items):
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                add_to_cart_order=item.add_to_cart_order or (i + 1),
                reordered=item.reordered or 0
            )
            session.add(order_item)

        session.commit()

        # Prepare response with order and items
        created_items = session.query(OrderItem).filter_by(order_id=order.order_id).all()
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "eval_set": order.eval_set,
            "order_number": order.order_number,
            "order_dow": order.order_dow,
            "order_hour_of_day": order.order_hour_of_day,
            "days_since_prior_order": order.days_since_prior_order,
            "total_items": order.total_items,
            "status": order.status,
            "phone_number": order.phone_number,
            "street_address": order.street_address,
            "city": order.city,
            "postal_code": order.postal_code,
            "country": order.country,
            "tracking_number": order.tracking_number,
            "shipping_carrier": order.shipping_carrier,
            "tracking_url": order.tracking_url,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "add_to_cart_order": item.add_to_cart_order,
                    "reordered": item.reordered,
                } for item in created_items
            ]
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating order")
    finally:
        session.close()

class AddOrderItemRequest(BaseModel):
    product_id: int
    quantity: int = 1
    add_to_cart_order: Optional[int] = None
    reordered: int = 0

@router.post("/{order_id}/items", status_code=201)
def add_order_items(
    order_id: str = Path(...),
    items: List[AddOrderItemRequest] = Body(...)
):
    session = SessionLocal()
    try:
        # Check order exists
        order = session.query(Order).filter_by(order_id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        if not items:
            raise HTTPException(status_code=400, detail="Must provide at least one item")

        # Validate product IDs exist
        product_ids = [item.product_id for item in items]
        existing_products = session.query(Product.product_id).filter(Product.product_id.in_(product_ids)).all()
        existing_product_ids = {p[0] for p in existing_products}
        missing_product_ids = [pid for pid in product_ids if pid not in existing_product_ids]
        if missing_product_ids:
            raise HTTPException(status_code=400, detail=f"Products not found: {', '.join(map(str, missing_product_ids))}")

        # Determine next add_to_cart_order
        current_count = session.query(OrderItem).filter_by(order_id=order_id).count()
        next_cart_order = current_count + 1

        # Add new order items
        added_items = []

        existing_items = session.query(OrderItem).filter_by(order_id=order_id).all()
        existing_map = {oi.product_id: oi for oi in existing_items}

        for item in items:
            if item.product_id in existing_map:
                existing = existing_map[item.product_id]
                # Update existing row
                existing.quantity += item.quantity
                # Optionally update add_to_cart_order, reordered, etc.
                added_items.append({
                    "order_id": order_id,
                    "product_id": item.product_id,
                    "quantity": existing.quantity,
                    "add_to_cart_order": existing.add_to_cart_order,
                    "reordered": existing.reordered,
                    "updated": True
                })
            else:
                new_item = OrderItem(
                    order_id=order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    add_to_cart_order=item.add_to_cart_order or next_cart_order,
                    reordered=item.reordered or 0
            )
                session.add(new_item)
                added_items.append({
                    "order_id": order_id,
                    "product_id": new_item.product_id,
                    "quantity": new_item.quantity,
                    "add_to_cart_order": new_item.add_to_cart_order,
                    "reordered": new_item.reordered,
                    "updated": False
                })
                next_cart_order += 1

        session.commit()
        return {
            "message": f"Added {len(added_items)} items to order {order_id}",
            "order_id": order_id,
            "added_items": added_items,
            "total_added": len(added_items)
        }
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error adding order items: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding order items")
    finally:
        session.close()

