# backend/app/routers/products.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models.base import APIResponse
from ..models.grocery import Product, ProductSearchResult, Department, Aisle
from ..services.database_service import db_service

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=APIResponse)
async def get_products(
    limit: int = Query(50, description="Number of products to return", ge=1, le=100),
    offset: int = Query(0, description="Number of products to skip", ge=0),
    categories: Optional[List[str]] = Query(None, description="Filter by department categories"),
    minPrice: Optional[float] = Query(None, description="Minimum price filter", ge=0),
    maxPrice: Optional[float] = Query(None, description="Maximum price filter", ge=0)
) -> APIResponse:
    """Get paginated list of products with optional filtering"""
    try:
        # Get products from database
        db_result = await db_service.get_products_with_filters(
            limit=limit, 
            offset=offset, 
            categories=categories,
            min_price=minPrice,
            max_price=maxPrice
        )
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        products_data = db_result.get("data", [])
        
        # Convert to Product models
        products = [
            Product(
                product_id=row["product_id"],
                product_name=row["product_name"],
                aisle_id=row["aisle_id"],
                department_id=row["department_id"],
                aisle_name=row.get("aisle_name"),
                department_name=row.get("department_name"),
                description=row.get("description"),
                price=row.get("price"),
                image_url=row.get("image_url")
            )
            for row in products_data
        ]
        
        # Get total count for pagination (simplified - would need separate count query in production)
        total_products = len(products_data)  # This is a limitation - we'd need a count query
        
        has_next = len(products) == limit  # Simplified check
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
    except HTTPException:
        raise
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
        
        # Get products from database with search
        db_result = await db_service.get_products_with_filters(
            limit=limit,
            offset=0,
            search_query=q
        )
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        products_data = db_result.get("data", [])
        
        # Convert to Product models
        products = [
            Product(
                product_id=row["product_id"],
                product_name=row["product_name"],
                aisle_id=row["aisle_id"],
                department_id=row["department_id"],
                aisle_name=row.get("aisle_name"),
                department_name=row.get("department_name"),
                description=row.get("description"),
                price=row.get("price"),
                image_url=row.get("image_url")
            )
            for row in products_data
        ]
        
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

@router.get("/department/{department_id}", response_model=APIResponse)
async def get_products_by_department(
    department_id: int,
    limit: int = Query(50, description="Number of products to return", ge=1, le=100),
    offset: int = Query(0, description="Number of products to skip", ge=0)
) -> APIResponse:
    """Get products in a specific department with pagination"""
    try:
        # Verify department exists
        dept_result = await db_service.get_department_by_id(department_id)
        
        if not dept_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        dept_data = dept_result.get("data", [])
        
        if not dept_data:
            raise HTTPException(status_code=404, detail=f"Department {department_id} not found")
        
        # Convert to Department model
        dept_row = dept_data[0]
        department = Department(
            id=str(dept_row["department_id"]),
            name=dept_row["department"]
        )
        
        # Get products in department with pagination
        db_result = await db_service.get_products_with_filters(
            limit=limit,
            offset=offset,
            department_id=department_id
        )
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        products_data = db_result.get("data", [])
        
        # Convert to Product models
        products = [
            Product(
                product_id=row["product_id"],
                product_name=row["product_name"],
                aisle_id=row["aisle_id"],
                department_id=row["department_id"],
                aisle_name=row.get("aisle_name"),
                department_name=row.get("department_name"),
                description=row.get("description"),
                price=row.get("price"),
                image_url=row.get("image_url")
            )
            for row in products_data
        ]
        
        # Pagination info
        has_next = len(products) == limit
        has_prev = offset > 0
        page = (offset // limit) + 1
        
        result = ProductSearchResult(
            products=products,
            total=len(products),  # Note: This is the current page count, not total
            page=page,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev
        )
        
        return APIResponse(
            message=f"Products in {department.name} department retrieved successfully",
            data={
                "department": department,
                "pagination": result
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
        aisle_result = await db_service.get_aisle_by_id(aisle_id)
        
        if not aisle_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        aisle_data = aisle_result.get("data", [])
        
        if not aisle_data:
            raise HTTPException(status_code=404, detail=f"Aisle {aisle_id} not found")
        
        # Convert to Aisle model
        aisle_row = aisle_data[0]
        aisle = Aisle(
            aisle_id=aisle_row["aisle_id"],
            aisle=aisle_row["aisle"]
        )
        
        # Get products in aisle
        products_result = await db_service.get_products_by_aisle(aisle_id)
        
        if not products_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        products_data = products_result.get("data", [])
        
        # Convert to Product models
        products = [
            Product(
                product_id=row["product_id"],
                product_name=row["product_name"],
                aisle_id=row["aisle_id"],
                department_id=row["department_id"],
                aisle_name=row.get("aisle_name"),
                department_name=row.get("department_name"),
                description=row.get("description"),
                price=row.get("price"),
                image_url=row.get("image_url")
            )
            for row in products_data
        ]
        
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

@router.get("/{product_id}", response_model=APIResponse)
async def get_product(product_id: int) -> APIResponse:
    """Get specific product by ID"""
    try:
        # Get product from database
        db_result = await db_service.get_product_by_id(product_id)
        
        if not db_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        products_data = db_result.get("data", [])
        
        if not products_data:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Convert to Product model
        product_row = products_data[0]
        product = Product(
            product_id=product_row["product_id"],
            product_name=product_row["product_name"],
            aisle_id=product_row["aisle_id"],
            department_id=product_row["department_id"],
            aisle_name=product_row.get("aisle_name"),
            department_name=product_row.get("department_name"),
            description=product_row.get("description"),
            price=product_row.get("price"),
            image_url=product_row.get("image_url")
        )
        
        return APIResponse(
            message="Product retrieved successfully",
            data=product
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
