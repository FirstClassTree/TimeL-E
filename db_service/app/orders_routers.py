# app/orders_routers.py
import datetime
from fastapi import APIRouter, Query, HTTPException, status, Body, Path, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc
from sqlalchemy import Enum as SqlEnum
from .db_core.database import SessionLocal
import asyncpg
from .db_core.models import Order, OrderItem, OrderStatus, Product, Department, Aisle, User
from pydantic import BaseModel
from typing import List, Optional
# Removed UUID imports since we're using integer user_ids and order_ids

router = APIRouter(prefix="/orders", tags=["orders"])

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int = 1

    # The order in which the item was added to the cart (useful for UI reordering, analytics, etc.)
    add_to_cart_order: Optional[int] = None

    reordered: int = 0

class CreateOrderRequest(BaseModel):
    user_id: int
    order_dow: int = None
    order_hour_of_day: int = None
    days_since_prior_order: Optional[int] = None
    total_items: int = None
    status: OrderStatus = OrderStatus.PENDING  # Enum enforced at validation
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    items: List[OrderItemRequest]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order_request: CreateOrderRequest, session: Session = Depends(get_db)):
    # db param is only used internally for dependency injection,
    # callers cannot provide their own db or alter it.

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

        # Get the most recent prior order by user
        last_order = session.execute(
            select(Order)
            .where(Order.user_id == order_request.user_id)
            .order_by(desc(Order.created_at))
            .limit(1)
        ).scalar_one_or_none()

        next_order_number = (last_order.order_number if last_order else 0) + 1
        # Get next available order_id (auto-increment would be better but this works)
        max_order_id = session.query(func.max(Order.order_id)).scalar() or 0
        next_order_id = max_order_id + 1

        days_since_prior_order = None

        if last_order:
            now = datetime.datetime.now(datetime.UTC)
            delta = now - last_order.created_at
            days_since_prior_order = int(delta.total_seconds() // 86400)  # in full days

        order = Order(
            user_id=order_request.user_id,
            order_id=next_order_id,
            order_number=next_order_number,
            order_dow=order_request.order_dow,
            order_hour_of_day=order_request.order_hour_of_day,
            days_since_prior_order=order_request.days_since_prior_order or days_since_prior_order,
            total_items=len(order_request.items),
            status=order_request.status,
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
        order_items = [
            OrderItem(
                order_id=order.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                add_to_cart_order=item.add_to_cart_order or (i + 1),
                reordered=item.reordered or 0
            )
            for i, item in enumerate(order_request.items)
        ]
        session.add_all(order_items)

        session.commit()

        # Prepare response with order and items
        # created_items = session.query(OrderItem).filter_by(order_id=order.order_id).all()
        session.refresh(order)  # Ensures order.items is populated (the relationship is up to date)
        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
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
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "add_to_cart_order": item.add_to_cart_order,
                    "reordered": item.reordered,
                } for item in order.items
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

class AddOrderItemRequest(BaseModel):
    product_id: int
    quantity: int = 1
    add_to_cart_order: Optional[int] = 0
    reordered: int = 0

@router.post("/{order_id}/items", status_code=201)
def add_order_items(
    order_id: int = Path(...),
    items: List[AddOrderItemRequest] = Body(...),
    session: Session = Depends(get_db)
):
    try:
        if not items:
            raise HTTPException(status_code=400, detail="Must provide at least one item")

        # Check order exists
        order = session.query(Order).filter_by(order_id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

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
        to_add = []

        existing_items = session.query(OrderItem).filter(
            OrderItem.order_id == order_id,
            OrderItem.product_id.in_(product_ids)
        ).all()
        existing_map = {oi.product_id: oi for oi in existing_items}

        for item in items:
            if item.product_id in existing_map:
                existing = existing_map[item.product_id]
                # Update existing row
                existing.quantity += item.quantity
                # changes are tracked automatically by SQLAlchemy
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
                to_add.append(new_item)
                added_items.append({
                    "order_id": order_id,
                    "product_id": new_item.product_id,
                    "quantity": new_item.quantity,
                    "add_to_cart_order": new_item.add_to_cart_order,
                    "reordered": new_item.reordered,
                    "updated": False
                })
                next_cart_order += 1

        # Bulk insert all new items at once
        if to_add:
            session.add_all(to_add)
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

@router.delete("/{order_id}", status_code=204)
# def delete_order(order_id: int, payload: DeleteUserRequest):
def delete_order(order_id: int):
    session = SessionLocal()
    try:
        order = session.query(Order).filter_by(order_id=order_id).first()
        user = session.query(User).filter_by(user_id=order.user_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(order)
        session.commit()
        return {"message": "Order deleted successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting order")
    finally:
        session.close()
