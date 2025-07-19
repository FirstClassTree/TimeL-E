# backend/app/services/ml_service.py
from typing import Dict, Any, Optional, List
from .base_client import ServiceClient
from ..config import settings

class MLService:
    """ML service client for TimeL-E ML predictions"""
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
    
    async def get_health(self) -> Dict[str, Any]:
        """Get ML service health status"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/health"
            )
    
    async def predict_for_user(self, user_id: str) -> Dict[str, Any]:
        """Get ML predictions for a user (main prediction endpoint)"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/predict/from-database",
                data={"user_id": user_id}
            )
    
    async def get_demo_prediction_comparison(self, user_id: int) -> Dict[str, Any]:
        """Get demo prediction with comparison to ground truth"""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/demo/prediction-comparison/{user_id}"
            )
    
    async def get_available_demo_users(self, limit: int = 100) -> Dict[str, Any]:
        """Get list of available demo users"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/demo-data/available-users?limit={limit}"
            )
    
    async def get_demo_user_order_history(self, user_id: int) -> Dict[str, Any]:
        """Get order history for a demo user"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/demo-data/instacart-user-order-history/{user_id}"
            )
    
    async def get_demo_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed statistics for a demo user"""
        async with ServiceClient() as client:
            return await client.request(
                method="GET",
                url=f"{self.base_url}/demo-data/user-stats/{user_id}"
            )
    
    async def evaluate_model(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Trigger model evaluation"""
        params = f"?sample_size={sample_size}" if sample_size else ""
        async with ServiceClient() as client:
            return await client.request(
                method="POST",
                url=f"{self.base_url}/evaluate-model{params}"
            )

    # Legacy methods for backward compatibility
    async def predict(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy predict method - maps to predict_for_user"""
        user_id = prediction_data.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in prediction_data")
        return await self.predict_for_user(user_id)
    
    async def get_recommendations(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Legacy recommendations method - maps to predict_for_user"""
        return await self.predict_for_user(user_id)

# Service instance
ml_service = MLService()
