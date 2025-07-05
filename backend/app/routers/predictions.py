# backend/app/routers/predictions.py
from fastapi import APIRouter, HTTPException, Query
from ..models.base import APIResponse
from ..models.grocery import UserPredictions, PredictionItem
from ..services.mock_data import mock_data

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_predictions(
    user_id: int,
    limit: int = Query(10, description="Number of predictions to return", ge=1, le=50)
) -> APIResponse:
    """Get ML predictions for a specific user"""
    try:
        # Get predictions from mock data service
        predictions_data = mock_data.get_user_predictions(user_id, limit=limit)
        
        # Convert to Pydantic models
        predictions = [
            PredictionItem(
                product_id=p["product_id"],
                product_name=p["product_name"], 
                score=round(p["score"], 3)
            )
            for p in predictions_data
        ]
        
        result = UserPredictions(
            user_id=user_id,
            predictions=predictions,
            total=len(predictions)
        )
        
        return APIResponse(
            message=f"Generated {len(predictions)} predictions for user {user_id}",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")
