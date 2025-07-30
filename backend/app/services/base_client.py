# backend/app/services/base_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
import json
from ..config import settings

class ServiceClient:
    """Base HTTP client for communicating with other services"""
    
    def __init__(self, timeout: int = None):
        self.timeout = timeout or settings.SERVICE_TIMEOUT
        self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
    
    async def request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to service"""
        
        if not self._client:
            raise RuntimeError("ServiceClient must be used as async context manager")
        
        # Default headers
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if headers:
            request_headers.update(headers)
        
        try:
            # Make the request
            if method.upper() == "GET":
                response = await self._client.get(
                    url, 
                    params=params, 
                    headers=request_headers
                )
            elif method.upper() == "POST":
                response = await self._client.post(
                    url, 
                    json=data, 
                    params=params, 
                    headers=request_headers
                )
            elif method.upper() == "PUT":
                response = await self._client.put(
                    url, 
                    json=data, 
                    params=params, 
                    headers=request_headers
                )
            elif method.upper() == "PATCH":
                response = await self._client.patch(
                    url, 
                    json=data, 
                    params=params, 
                    headers=request_headers
                )
            elif method.upper() == "DELETE":
                if data:    # httpx.delete() doesn't support JSON body; using .request() with content instead
                    response = await self._client.request(
                        method="DELETE",
                        url=url,
                        content=json.dumps(data),
                        headers=request_headers,
                        params=params
                    )
                else:
                    response = await self._client.delete(
                        url=url,
                        params=params,
                        headers=request_headers
                    )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors
            error_detail = f"HTTP {e.response.status_code} error"
            try:
                error_body = e.response.json()
                if "detail" in error_body:
                    error_detail = error_body["detail"]
                elif "message" in error_body:
                    error_detail = error_body["message"]
            except:
                error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
            
            raise Exception(f"Service request failed: {error_detail}")
            
        except httpx.RequestError as e:
            # Handle connection errors
            raise Exception(f"Service connection failed: {str(e)}")
        
        except Exception as e:
            # Handle other errors
            raise Exception(f"Service request error: {str(e)}")
