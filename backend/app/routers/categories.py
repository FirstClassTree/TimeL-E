# backend/app/routers/categories.py
from fastapi import APIRouter, HTTPException
from ..models.base import APIResponse
from ..models.grocery import Department, Aisle
from ..services.mock_data import mock_data

router = APIRouter(prefix="/api", tags=["Categories"])

# Department endpoints
@router.get("/departments", response_model=APIResponse)
async def get_departments() -> APIResponse:
    """Get all departments"""
    try:
        departments = mock_data.get_departments()
        
        return APIResponse(
            message="Departments retrieved successfully",
            data={
                "departments": departments,
                "total": len(departments)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments/{department_id}", response_model=APIResponse)
async def get_department(department_id: int) -> APIResponse:
    """Get specific department"""
    try:
        department = mock_data.get_department(department_id)
        if not department:
            raise HTTPException(status_code=404, detail=f"Department {department_id} not found")
        
        # Get product count for this department
        products = mock_data.get_products_by_department(department_id)
        
        return APIResponse(
            message="Department retrieved successfully",
            data={
                "department": department,
                "product_count": len(products)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Aisle endpoints
@router.get("/aisles", response_model=APIResponse)
async def get_aisles() -> APIResponse:
    """Get all aisles"""
    try:
        aisles = mock_data.get_aisles()
        
        return APIResponse(
            message="Aisles retrieved successfully",
            data={
                "aisles": aisles,
                "total": len(aisles)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aisles/{aisle_id}", response_model=APIResponse)
async def get_aisle(aisle_id: int) -> APIResponse:
    """Get specific aisle"""
    try:
        aisle = mock_data.get_aisle(aisle_id)
        if not aisle:
            raise HTTPException(status_code=404, detail=f"Aisle {aisle_id} not found")
        
        # Get product count for this aisle
        products = mock_data.get_products_by_aisle(aisle_id)
        
        return APIResponse(
            message="Aisle retrieved successfully",
            data={
                "aisle": aisle,
                "product_count": len(products)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments/{department_id}/aisles", response_model=APIResponse)
async def get_aisles_by_department(department_id: int) -> APIResponse:
    """Get all aisles in a specific department"""
    try:
        # Verify department exists
        department = mock_data.get_department(department_id)
        if not department:
            raise HTTPException(status_code=404, detail=f"Department {department_id} not found")
        
        # Get all products in this department to find unique aisles
        products = mock_data.get_products_by_department(department_id)
        aisle_ids = list(set(p.aisle_id for p in products))
        
        # Get aisle details
        aisles = []
        for aisle_id in aisle_ids:
            aisle = mock_data.get_aisle(aisle_id)
            if aisle:
                aisle_data = aisle.dict()
                # Add product count for this aisle within this department
                aisle_products = [p for p in products if p.aisle_id == aisle_id]
                aisle_data["product_count"] = len(aisle_products)
                aisles.append(aisle_data)
        
        # Sort by aisle name
        aisles.sort(key=lambda x: x["aisle"])
        
        return APIResponse(
            message=f"Found {len(aisles)} aisles in {department.department} department",
            data={
                "department": department,
                "aisles": aisles,
                "total": len(aisles)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Summary endpoint for navigation
@router.get("/categories/summary", response_model=APIResponse)
async def get_categories_summary() -> APIResponse:
    """Get summary of all categories with counts"""
    try:
        departments = mock_data.get_departments()
        aisles = mock_data.get_aisles()
        
        # Add product counts to departments
        dept_summary = []
        for dept in departments:
            products = mock_data.get_products_by_department(dept.department_id)
            dept_data = dept.dict()
            dept_data["product_count"] = len(products)
            dept_summary.append(dept_data)
        
        # Add product counts to aisles
        aisle_summary = []
        for aisle in aisles:
            products = mock_data.get_products_by_aisle(aisle.aisle_id)
            aisle_data = aisle.dict()
            aisle_data["product_count"] = len(products)
            aisle_summary.append(aisle_data)
        
        return APIResponse(
            message="Categories summary retrieved successfully",
            data={
                "departments": {
                    "items": dept_summary,
                    "total": len(dept_summary)
                },
                "aisles": {
                    "items": aisle_summary,
                    "total": len(aisle_summary)
                },
                "total_products": len(mock_data.products)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
