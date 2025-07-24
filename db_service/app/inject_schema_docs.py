# app/db_core/inject_schema_docs.py

"""Make db docs accessible w/o exposing the route."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from .db_core.models.pydantic_models_for_docs import User, Product, Department, Aisle, ProductEnriched, OrderItem, CartItem, Cart, Order, OrderStatus

router = APIRouter(tags=["Database Schemas"])

class _SchemaReference(BaseModel):
    user: Optional[User]
    product: Optional[Product]
    department: Optional[Department]
    aisle: Optional[Aisle]
    product_enriched: Optional[ProductEnriched]
    order_item: Optional[OrderItem]
    cart_item: Optional[CartItem]
    cart: Optional[Cart]
    order: Optional[Order]
    order_status: Optional[OrderStatus]

def deny_access():
    """Used as dependency to hide schema route from use"""
    raise HTTPException(status_code=404)

@router.get(
     "/_doc_ref/_internal_schemas",
    response_model=None,
    dependencies=[Depends(deny_access)],
    tags=["Database Schemas"]
)
def _doc_schema_injector():
    """
    Injects all Pydantic models into OpenAPI docs for reference.
    This endpoint is hidden and always returns 404.
    """
    _ = (
        User.model_json_schema(),
        Product.model_json_schema(),
        Department.model_json_schema(),
        Aisle.model_json_schema(),
        ProductEnriched.model_json_schema(),
        OrderItem.model_json_schema(),
        CartItem.model_json_schema(),
        Cart.model_json_schema(),
        Order.model_json_schema(),
        OrderStatus.model_json_schema()
    )

