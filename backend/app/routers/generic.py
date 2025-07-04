# backend/app/routers/generic.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from ..models.base import APIResponse, ErrorResponse, GenericEntity
from ..services.http_client import db_service

router = APIRouter(prefix="/api", tags=["Generic CRUD"])

@router.post("/{entity}")
async def create_entity(entity: str, data: Dict[str, Any]) -> APIResponse:
    """Create any entity type with generic JSON data"""
    try:
        result = await db_service.create_entity(entity, data)
        return APIResponse(
            message=f"{entity.capitalize()} created successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity}")
async def list_entities(
    entity: str,
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: Optional[int] = Query(None, description="Offset for pagination"),
    **filters: Dict[str, Any]
) -> APIResponse:
    """List entities with optional filtering and pagination"""
    try:
        # Build filters from query parameters
        query_filters = {}
        if limit is not None:
            query_filters["limit"] = limit
        if offset is not None:
            query_filters["offset"] = offset
        
        # Add any additional filter parameters
        for key, value in filters.items():
            if key not in ["limit", "offset"]:
                query_filters[key] = value
        
        result = await db_service.list_entities(entity, query_filters)
        return APIResponse(
            message=f"{entity.capitalize()} retrieved successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity}/{entity_id}")
async def get_entity(entity: str, entity_id: str) -> APIResponse:
    """Get specific entity by ID"""
    try:
        result = await db_service.get_entity(entity, entity_id)
        return APIResponse(
            message=f"{entity.capitalize()} retrieved successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{entity}/{entity_id}")
async def update_entity(entity: str, entity_id: str, data: Dict[str, Any]) -> APIResponse:
    """Update specific entity by ID"""
    try:
        result = await db_service.update_entity(entity, entity_id, data)
        return APIResponse(
            message=f"{entity.capitalize()} updated successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{entity}/{entity_id}")
async def delete_entity(entity: str, entity_id: str) -> APIResponse:
    """Delete specific entity by ID"""
    try:
        result = await db_service.delete_entity(entity, entity_id)
        return APIResponse(
            message=f"{entity.capitalize()} deleted successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
