# backend/app/routers/predictions.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from ..models.base import APIResponse
from ..models.grocery import UserPredictions, PredictionItem
from ..services.database_service import db_service

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_predictions(
    user_id: str,
    limit: int = Query(10, description="Number of predictions to return", ge=1, le=50),
    offset: int = Query(0, description="Number of predictions to skip", ge=0)
) -> APIResponse:
    """Get ML predictions for a specific user with pagination"""
    try:
        # Verify user exists
        user_result = await db_service.get_user_by_id(user_id)
        if not user_result.get("success", True) or not user_result.get("data", []):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get user's order history to generate predictions
        orders_result = await db_service.get_user_orders_with_filters(
            user_id=user_id,
            limit=100,  # Get recent orders for ML analysis
            offset=0
        )
        
        orders_data = orders_result.get("data", []) if orders_result.get("success", True) else []
        
        # Generate predictions based on order history
        predictions_data = await _generate_user_predictions(user_id, orders_data, limit, offset)
        
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
            data={
                **result.dict(),
                "page": (offset // limit) + 1,
                "per_page": limit,
                "has_next": len(predictions) == limit,
                "has_prev": offset > 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")

async def _generate_user_predictions(user_id: str, orders_data: list, limit: int, offset: int) -> list:
    """Generate ML predictions for user based on order history"""
    try:
        # Analyze user's purchase history
        purchased_products = set()
        department_preferences = {}
        
        # Extract patterns from order history
        for order in orders_data:
            # Get items for each order
            items_result = await db_service.get_order_items(str(order["order_id"]))
            items_data = items_result.get("data", []) if items_result.get("success", True) else []
            
            for item in items_data:
                purchased_products.add(item["product_id"])
                
                # Get product details to analyze department preferences
                product_result = await db_service.get_product_by_id(item["product_id"])
                if product_result.get("success", True) and product_result.get("data", []):
                    product = product_result["data"][0]
                    dept_id = product["department_id"]
                    department_preferences[dept_id] = department_preferences.get(dept_id, 0) + 1
        
        # Find top preferred departments
        top_departments = sorted(department_preferences.items(), key=lambda x: x[1], reverse=True)[:3]
        
        predictions = []
        
        # Generate predictions from preferred departments
        for dept_id, _ in top_departments:
            dept_products_result = await db_service.get_products_by_department(dept_id)
            if dept_products_result.get("success", True):
                dept_products = dept_products_result.get("data", [])
                
                for product in dept_products:
                    if product["product_id"] not in purchased_products:
                        # Calculate prediction score based on department preference
                        base_score = department_preferences.get(dept_id, 0) / sum(department_preferences.values())
                        # Add some randomness for diversity
                        import random
                        random.seed(hash(f"{user_id}-{product['product_id']}"))  # Consistent randomness
                        final_score = base_score + random.uniform(-0.1, 0.1)
                        final_score = max(0.1, min(1.0, final_score))  # Clamp between 0.1 and 1.0
                        
                        predictions.append({
                            "product_id": product["product_id"],
                            "product_name": product["product_name"],
                            "score": final_score
                        })
        
        # If user has no history, recommend popular products across all departments
        if not predictions:
            # Get some popular products (simplified - just get first N products)
            popular_result = await db_service.get_products_with_filters(limit=limit*2, offset=0)
            if popular_result.get("success", True):
                popular_products = popular_result.get("data", [])
                
                import random
                random.seed(hash(user_id))  # Consistent for same user
                
                for product in popular_products:
                    predictions.append({
                        "product_id": product["product_id"],
                        "product_name": product["product_name"],
                        "score": random.uniform(0.3, 0.7)  # Medium confidence for new users
                    })
        
        # Sort by score and apply pagination
        predictions.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply offset and limit
        paginated_predictions = predictions[offset:offset + limit]
        
        return paginated_predictions
        
    except Exception as e:
        # Fallback to basic recommendations if ML generation fails
        fallback_result = await db_service.get_products_with_filters(limit=limit, offset=offset)
        if fallback_result.get("success", True):
            products = fallback_result.get("data", [])
            
            import random
            random.seed(hash(user_id))
            
            return [
                {
                    "product_id": product["product_id"],
                    "product_name": product["product_name"],
                    "score": random.uniform(0.2, 0.5)  # Low confidence fallback
                }
                for product in products
            ]
        
        return []
