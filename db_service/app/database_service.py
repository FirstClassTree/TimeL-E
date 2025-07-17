# app/database_service.py

from fastapi import APIRouter, Query, HTTPException, Request, status, Body, Path
from fastapi.responses import JSONResponse
import psycopg2
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.database import SessionLocal
import asyncpg
from app.models import Order, OrderItem, OrderStatus, Product, Department, Aisle, User
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid_utils import uuid7
# from uuid import uuid7   # native uuid7 in python 3.14
import uuid

router = APIRouter()

DATABASE_URL = os.environ.get("DATABASE_URL")

def validate_params(params):
    """Reject malformed inputs or strange usage."""
    if not isinstance(params, list):
        raise ValueError("Params must be a list")
    for p in params:
        if isinstance(p, (dict, list, set, tuple, bytes, bytearray)):
            raise ValueError(f"Disallowed param type: {type(p)}")
        if callable(p):
            raise ValueError("Function values not allowed in params")
        if isinstance(p, str) and len(p) > 10000:
            raise ValueError("String parameter too long")

@router.get("/health")
def health_check():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return {"status": "ok", "database": "reachable"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

@router.post("/query")
async def run_query(request: Request):
    """
    Accepts parameterized SQL queries in PostgreSQL style ($1, $2, ...) with a list of parameters.
    Expects JSON: { "sql": "SELECT ... WHERE ...", "params": [...] }
    """
    # """
    # Accepts parameterized SQL SELECT queries in PostgreSQL style ($1, $2, ...) with a list of parameters.
    # Expects JSON: { "sql": "SELECT ... WHERE ...", "params": [...] }
    # Only SELECT queries are allowed.
    # """
    body = await request.json()
    sql = body.get("sql")
    params = body.get("params", [])

    if not sql:
        raise HTTPException(status_code=400, detail="Missing 'sql' in request body")

    # if not sql.strip().lower().startswith("select"):
    #     raise HTTPException(status_code=403, detail="Only SELECT queries are allowed")

    try:
        validate_params(params) # protects against malformed inputs or strange usage
        # asyncpg expects $1/$2, but parameters should be passed as *args
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(sql, *params)
            # Convert Record objects to dicts for JSON serialization
            results = [dict(row) for row in rows]
        except Exception as query_exc:
            print(f"Query failed: {query_exc}")   # print goes to container logs
            raise HTTPException(status_code=400, detail=f"Database query failed.")
        finally:
            await conn.close()
        return {"status": "ok", "results": results}
    except Exception as e:
        print(f"Request failed: {e}")
        raise HTTPException(status_code=400, detail=f"Request failed.")

@router.get("/products")
def get_products(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    categories: list[str] = Query(default=None)
) -> JSONResponse:
    """Return a paginated list of products from the database with department and aisle names,
    optionally filtered by department (categories)."""
    session = SessionLocal()
    try:
        # Start building base query with eager loading
        query = (
            session.query(Product)
            .options(
                joinedload(Product.department),
                joinedload(Product.aisle)
            )
        )

        # Filter by department name if categories param provided
        if categories:
            query = query.join(Product.department).filter(
                Department.department.in_([c.lower() for c in categories])
            )

        # Count all products after filtering (for pagination UI)
        total = query.count()

        products = (
            query.order_by(Product.product_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        results = [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "department_id": p.department_id,
                "department_name": p.department.department if p.department else None,
                "aisle_id": p.aisle_id,
                "aisle_name": p.aisle.aisle if p.aisle else None,
            }
            for p in products
        ]
        return JSONResponse(
            content={
                "products": results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
                "has_prev": offset > 0,
            }
        )
    except Exception as e:
        print(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Error fetching products")
    finally:
        session.close()


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


@router.post("/orders", status_code=status.HTTP_201_CREATED)
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


@router.post("/orders/{order_id}/items", status_code=201)
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
