# backend/app/services/ml_service.py
from typing import Dict, Any, Optional
from .base_client import ServiceClient
from ..config import settings

class MLService:
    """ML service client"""
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
    
    async def predict(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get ML predictions"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/predict",
                data=prediction_data
            )
    
    async def get_recommendations(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get product recommendations for user"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/recommendations",
                data={"user_id": user_id, "context": context or {}}
            )
    
    async def train_model(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger model training with new data"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/train",
                data=training_data
            )
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about current ML model"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/model/info"
            )
    
    async def analyze_user_behavior(self, user_id: str, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/analyze/behavior",
                data={"user_id": user_id, "behavior": behavior_data}
            )

# Service instance
ml_service = MLService()
