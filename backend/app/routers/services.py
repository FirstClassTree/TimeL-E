# backend/app/routers/services.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..models.base import APIResponse, ServiceRequest
from ..services.http_client import db_service, ml_service

router = APIRouter(prefix="/services", tags=["Service Coordination"])

@router.post("/db/query")
async def forward_db_query(query_data: Dict[str, Any]) -> APIResponse:
    """Forward complex queries to database service"""
    try:
        result = await db_service.query(query_data)
        return APIResponse(
            message="Database query executed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ml/predict")
async def forward_ml_prediction(prediction_data: Dict[str, Any]) -> APIResponse:
    """Forward prediction requests to ML service"""
    try:
        result = await ml_service.predict(prediction_data)
        return APIResponse(
            message="ML prediction completed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def check_services_health() -> APIResponse:
    """Check health status of all connected services"""
    service_status = {
        "database": "unknown",
        "ml": "unknown",
        "api_gateway": "healthy"
    }
    
    # Check database service
    try:
        await db_service.list_entities("health", {"limit": 1})
        service_status["database"] = "healthy"
    except Exception as e:
        service_status["database"] = f"unhealthy: {str(e)}"
    
    # Check ML service
    try:
        await ml_service.predict({"test": "health_check"})
        service_status["ml"] = "healthy"
    except Exception as e:
        service_status["ml"] = f"unhealthy: {str(e)}"
    
    overall_health = all(
        status == "healthy" for status in service_status.values()
    )
    
    return APIResponse(
        message="Service health check completed",
        data={
            "overall_status": "healthy" if overall_health else "degraded",
            "services": service_status
        }
    )
