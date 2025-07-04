# backend/app/routers/products.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models.base import APIResponse
from ..models.grocery import Product, ProductSearchResult
from ..services.mock_data import mock_data

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/", response_model=APIResponse)
async def get_products(
    limit: int = Query(50, description="Number of products to return", ge=1, le=100),
    offset: int = Query(0, description="Number of products to skip", ge=0)
) -> APIResponse:
    """Get paginated list of products"""
    try:
        products = mock_data.get_products(limit=limit, offset=offset)
        total_products = len(mock_data.products)
        
        has_next = (offset + limit) < total_products
        has_prev = offset > 0
        page = (offset // limit) + 1
        
        result = ProductSearchResult(
            products=products,
            total=total_products,
            page=page,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev
        )
        
        return APIResponse(
            message="Products retrieved successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=APIResponse)
async def search_products(
    q: str = Query(..., description="Search query for product names"),
    limit: int = Query(50, description="Number of results to return", ge=1, le=100)
) -> APIResponse:
    """Search products by name"""
    try:
        if len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        products = mock_data.search_products(q, limit=limit)
        
        result = ProductSearchResult(
            products=products,
            total=len(products),
            page=1,
            per_page=limit,
            has_next=False,
            has_prev=False
        )
        
        return APIResponse(
            message=f"Found {len(products)} products matching '{q}'",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}", response_model=APIResponse)
async def get_product(product_id: int) -> APIResponse:
    """Get specific product by ID"""
    try:
        product = mock_data.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        return APIResponse(
            message="Product retrieved successfully",
            data=product
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/department/{department_id}", response_model=APIResponse)
async def get_products_by_department(department_id: int) -> APIResponse:
    """Get all products in a specific department"""
    try:
        # Verify department exists
        department = mock_data.get_department(department_id)
        if not department:
            raise HTTPException(status_code=404, detail=f"Department {department_id} not found")
        
        products = mock_data.get_products_by_department(department_id)
        
        return APIResponse(
            message=f"Products in {department.department} department retrieved successfully",
            data={
                "department": department,
                "products": products,
                "total": len(products)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aisle/{aisle_id}", response_model=APIResponse)
async def get_products_by_aisle(aisle_id: int) -> APIResponse:
    """Get all products in a specific aisle"""
    try:
        # Verify aisle exists
        aisle = mock_data.get_aisle(aisle_id)
        if not aisle:
            raise HTTPException(status_code=404, detail=f"Aisle {aisle_id} not found")
        
        products = mock_data.get_products_by_aisle(aisle_id)
        
        return APIResponse(
            message=f"Products in {aisle.aisle} aisle retrieved successfully",
            data={
                "aisle": aisle,
                "products": products,
                "total": len(products)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
