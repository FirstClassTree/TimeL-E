# backend/app/routers/predictions.py
from fastapi import APIRouter, HTTPException
from typing import List
from ..models.base import APIResponse
from ..models.grocery import PredictionItem, UserPredictions
from ..services.ml_service import ml_service

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_predictions(user_id: str) -> APIResponse:
    """Get ML predictions for a user - clean and simple"""
    try:
        # Direct call to ML service
        ml_result = await ml_service.predict_for_user(user_id)
        
        # Check if we got a successful response with predicted_cart
        if ml_result.get("success") and "predicted_cart" in ml_result:
            predicted_cart = ml_result["predicted_cart"]
            
            # Convert to our response format
            predictions: List[PredictionItem] = [
                PredictionItem(
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    score=0.8  # Default confidence score
                )
                for item in predicted_cart
            ]
            
            user_predictions = UserPredictions(
                user_id=user_id,
                predictions=predictions,
                total=len(predictions)
            )
            
            return APIResponse(
                message=f"Generated {len(predictions)} ML predictions for user {user_id}",
                data=user_predictions.dict()
            )
        
        else:
            # Handle case where ML service returns no predictions
            return APIResponse(
                message=f"No predictions available for user {user_id}",
                data=UserPredictions(
                    user_id=user_id,
                    predictions=[],
                    total=0
                ).dict()
            )
            
    except Exception as e:
        # Handle any errors from ML service or processing
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get predictions for user {user_id}: {str(e)}"
        )
