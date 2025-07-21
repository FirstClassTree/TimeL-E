# backend/app/services/ml_service.py
from typing import Dict, Any
from .base_client import ServiceClient
from ..config import settings

class MLService:
    """Clean ML service client for TimeL-E ML predictions"""
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
    
    async def predict_for_user(self, user_id: str) -> Dict[str, Any]:
        """Get ML predictions for a user - calls clean ML endpoint"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/predict/{user_id}",
                data={}  # Empty data for POST request
            )

# Service instance
ml_service = MLService()
