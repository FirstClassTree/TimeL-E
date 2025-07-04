# backend/app/services/database_service.py
from typing import Dict, Any, Optional
from .base_client import ServiceClient
from ..config import settings

class DatabaseService:
    """Database service client"""
    
    def __init__(self):
        self.base_url = settings.DB_SERVICE_URL
    
    async def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity in database"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/{entity_type}",
                data=data
            )
    
    async def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Get entity from database"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/{entity_type}/{entity_id}"
            )
    
    async def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity in database"""
        async with ServiceClient() as client:
            return await client.request(
                method="PUT",
                url=f"{self.base_url}/{entity_type}/{entity_id}",
                data=data
            )
    
    async def delete_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Delete entity from database"""
        async with ServiceClient() as client:
            return await client.request(
                method="DELETE",
                url=f"{self.base_url}/{entity_type}/{entity_id}"
            )
    
    async def list_entities(self, entity_type: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List entities from database"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/{entity_type}",
                params=filters
            )
    
    async def query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom query"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/query",
                data=query_data
            )

# Service instance
db_service = DatabaseService()
