# backend/app/services/base_client.py
import httpx
from typing import Dict, Any, Optional
from ..config import settings

class ServiceClient:
    """Async HTTP client for inter-service communication"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(settings.SERVICE_TIMEOUT)
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to external service"""
        try:
            if not self.client:
                raise RuntimeError("Client not initialized. Use async context manager.")
            
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers or {"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise Exception(f"Service timeout: {url}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Service error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Service communication error: {str(e)}")
