# backend/app/routers/predictions.py
from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from ..models.base import APIResponse
from ..models.grocery import PredictionItem, UserPredictions
from ..services.ml_service import ml_service
from ..services.database_service import db_service

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_predictions(user_id: UUID) -> APIResponse:
    """Get ML predictions for a user using external UUID"""
    try:
        # First, translate external UUID to internal user ID
        print(f"DEBUG: Looking up user with UUID: {user_id}")
        user_lookup = await db_service.get_internal_user_id_by_external_uuid(str(user_id))
        print(f"DEBUG: User lookup result: {user_lookup}")
        
        # Check if user exists
        if not user_lookup.get("success", True) or not user_lookup.get("data"):
            raise HTTPException(
                status_code=404, 
                detail=f"User not found with UUID: {user_id}"
            )
        
        # Get the internal user ID
        user_data = user_lookup["data"][0]
        internal_user_id = user_data["id"]
        print(f"DEBUG: Internal user ID: {internal_user_id} (type: {type(internal_user_id)})")
        
        # Call ML service with internal user ID
        print(f"DEBUG: Calling ML service with user ID: {internal_user_id}")
        ml_result = await ml_service.predict_for_user(internal_user_id)
        
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
                user_id=str(user_id),
                predictions=predictions,
                total=len(predictions)
            )
            
            return APIResponse(
                message=f"Generated {len(predictions)} ML predictions for user {user_id}",
                data=user_predictions.model_dump(by_alias=True)
            )
        
        else:
            # Handle case where ML service returns no predictions
            return APIResponse(
                message=f"No predictions available for user {user_id}",
                data=UserPredictions(
                    user_id=str(user_id),
                    predictions=[],
                    total=0
                ).model_dump(by_alias=True)
            )
            
    except Exception as e:
        # Handle any errors from ML service or processing
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get predictions for user {user_id}: {str(e)}"
        )
