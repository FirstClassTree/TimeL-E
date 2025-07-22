# app/database_service.py

from fastapi import APIRouter, Query, HTTPException, Request
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.database import SessionLocal
import asyncpg
from app.models import Order, OrderItem, OrderStatus, Product, Department, Aisle, User, ProductEnriched
from app.config import settings
from pydantic import BaseModel
from typing import List, Optional
# Removed UUID imports since we're using integer user_ids and order_ids

router = APIRouter()

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
        import psycopg2
        conn = psycopg2.connect(settings.DATABASE_URL)
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
        conn = await asyncpg.connect(settings.DATABASE_URL)
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
):
    """Return a paginated list of products from the database with department and aisle names,
    optionally filtered by department (categories)."""
    session = SessionLocal()
    try:
        # Start building base query with eager loading including ProductEnriched
        query = (
            session.query(Product, ProductEnriched)
            .outerjoin(ProductEnriched, Product.product_id == ProductEnriched.product_id)
            .join(Product.department)
            .join(Product.aisle)
        )

        # Filter by department name if categories param provided
        if categories:
            query = query.filter(
                func.lower(Department.department).in_([c.lower() for c in categories])
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
                "description": pe.description if pe else None,
                "price": float(pe.price) if pe and pe.price else None,
                "image_url": pe.image_url if pe else None,
            }
            for p, pe in products
        ]
        return {
            "products": results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_prev": offset > 0,
            }
    except Exception as e:
        print(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Error fetching products")
    finally:
        session.close()
