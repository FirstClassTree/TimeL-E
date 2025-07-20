# backend/app/routers/categories.py
from fastapi import APIRouter, HTTPException
from ..models.base import APIResponse
from ..models.grocery import Department
from ..services.database_service import db_service

router = APIRouter(prefix="/api", tags=["Categories"])

# Department endpoints
@router.get("/departments", response_model=APIResponse)
async def get_departments() -> APIResponse:
    """Get all departments"""
    try:
        # Get departments from database
        departments_result = await db_service.get_all_departments()
        
        if not departments_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        departments_data = departments_result.get("data", [])
        
        # Convert to Department model format
        departments = []
        for dept_row in departments_data:
            department = Department(
                id=str(dept_row["department_id"]),
                name=dept_row["department"],
                description=None,
                imageUrl=None,
                parentId=None
            )
            departments.append(department)
        
        return APIResponse(
            message="Departments retrieved successfully",
            data={
                "departments": [dept.dict() for dept in departments],
                "total": len(departments)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments/{department_id}", response_model=APIResponse)
async def get_department(department_id: int) -> APIResponse:
    """Get specific department"""
    try:
        # Get department from database
        department_result = await db_service.get_department_by_id(department_id)
        
        if not department_result.get("success", True):
            raise HTTPException(status_code=500, detail="Database query failed")
        
        department_data = department_result.get("data", [])
        
        if not department_data:
            raise HTTPException(status_code=404, detail=f"Department {department_id} not found")
        
        # Convert to Department model format
        dept_row = department_data[0]
        department = Department(
            id=str(dept_row["department_id"]),
            name=dept_row["department"],
            description=None,
            imageUrl=None,
            parentId=None
        )
        
        # Get product count for this department
        products_result = await db_service.get_products_by_department(department_id)
        product_count = len(products_result.get("data", []))
        
        return APIResponse(
            message="Department retrieved successfully",
            data={
                "department": department.dict(),
                "product_count": product_count
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
