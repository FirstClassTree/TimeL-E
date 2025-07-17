# ml-service/src/api/main.py
# FIXED VERSION: Properly handles database predictions for seeded users

import os
import json
import pandas as pd
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

from ..models.stacked_basket_model import StackedBasketModel
from ..services.prediction import EnhancedPredictionService
from ..features.engineering import UnifiedFeatureEngineer as DatabaseFeatureEngineer
from ..core.evaluator import BasketPredictionEvaluator
from ..core.logger import setup_logger
from ..data.connection import test_database_connection, get_db_session
from ..data.models import User

logger = setup_logger(__name__)

# ============================================================================
# ENVIRONMENT VARIABLES (Loaded from .env file)
# ============================================================================

MODEL_PATH_BASE = os.getenv("MODEL_PATH_BASE", "/app/models")
PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "/app/training-data/processed")
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", "/app/training-data")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://timely_user:timely_password@postgres:5432/timely_db")
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
EVALUATION_SAMPLE_SIZE = int(os.getenv("EVALUATION_SAMPLE_SIZE", "100"))

logger.info(f"ML Service starting - Model Path: {MODEL_PATH_BASE}")
logger.info(f"Environment: {os.getenv('NODE_ENV', 'development')}")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PredictionRequest(BaseModel):
    user_id: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    database_available: bool
    architecture: str
    feature_engineering: str
    data_loaded: Dict[str, int]

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager - loads from .env automatically."""
    logger.info("🚀 Starting Timely ML Service...")
    
    # Test database connection
    app.state.database_available = test_database_connection()
    if app.state.database_available:
        logger.info("✅ Database connection successful")
    else:
        logger.warning("⚠️ Database connection failed - demo mode only")
    
    # Load and initialize model
    app.state.model = StackedBasketModel()
    try:
        app.state.model.load_models(MODEL_PATH_BASE)
        logger.info(f"✅ StackedBasketModel loaded from {MODEL_PATH_BASE}")
        app.state.model_loaded = True
    except Exception as e:
        logger.error(f"🚨 ML model loading failed: {e}")
        app.state.model = None
        app.state.model_loaded = False
    
    # Initialize prediction service for database-driven predictions
    if app.state.model and app.state.database_available:
        app.state.prediction_service = EnhancedPredictionService(app.state.model, PROCESSED_DATA_PATH)
        logger.info("✅ EnhancedPredictionService initialized")
    else:
        app.state.prediction_service = None
        logger.warning("⚠️ Prediction service not available")
    
    # Initialize feature engineer for CSV-based demo operations
    app.state.demo_feature_engineer = DatabaseFeatureEngineer(PROCESSED_DATA_PATH)
    logger.info("✅ DatabaseFeatureEngineer initialized for demo operations")
    
    # Load raw CSV data for demo mode
    app.state.data_loaded = {}
    try:
        logger.info(f"Loading CSV data from {RAW_DATA_PATH}")
        
        # Load raw Instacart data
        app.state.orders_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "orders.csv"))
        app.state.order_products_prior_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "order_products__prior.csv"))
        app.state.order_products_train_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "order_products__train.csv"))
        app.state.products_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "products.csv"))
        
        # Load processed data
        app.state.instacart_future_df = pd.read_csv(os.path.join(PROCESSED_DATA_PATH, "instacart_future.csv"))
        
        # Store counts
        app.state.data_loaded = {
            "orders": len(app.state.orders_df),
            "prior_products": len(app.state.order_products_prior_df),
            "train_products": len(app.state.order_products_train_df),
            "products": len(app.state.products_df),
            "future_baskets": len(app.state.instacart_future_df)
        }
        
        logger.info(f"✅ CSV data loaded successfully: {app.state.data_loaded}")
        
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")
        app.state.data_loaded = {"error": str(e)}
    
    yield
    
    # Cleanup
    logger.info("Shutting down ML Service...")

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Timely ML Service",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH & STATUS ENDPOINTS (CONSOLIDATED)
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Consolidated health check endpoint."""
    return HealthResponse(
        status="healthy" if app.state.model_loaded else "degraded",
        model_loaded=app.state.model_loaded,
        database_available=app.state.database_available,
        architecture="direct_database_access",
        feature_engineering="unified",
        data_loaded=app.state.data_loaded
    )

# ============================================================================
# CORE PREDICTION ENDPOINTS
# ============================================================================

@app.post("/predict/from-database", tags=["Prediction"])
async def predict_from_database(request: PredictionRequest):
    """
    DEMAND 1: Main prediction endpoint using user's history from the database.
    FIXED: Now properly handles UUID-based users and checks for demo users.
    """
    if not app.state.prediction_service:
        raise HTTPException(status_code=503, detail="Prediction service not available")
    
    try:
        logger.info(f"Database prediction request for user: {request.user_id}")
        
        # CRITICAL FIX: Check if this is a demo user with Instacart data
        with get_db_session() as session:
            user = session.query(User).filter(User.id == request.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User {request.user_id} not found")
            
            # Check if user has metadata with original Instacart ID
            instacart_user_id = None
            if user.metadata and isinstance(user.metadata, dict):
                instacart_user_id = user.metadata.get('instacart_user_id')
            
            if instacart_user_id:
                # This is a demo user - use CSV data for prediction
                logger.info(f"Demo user detected with Instacart ID: {instacart_user_id}")
                
                # Use the demo feature engineer with CSV data
                features_df = app.state.demo_feature_engineer.generate_features_from_csv_data(
                    str(instacart_user_id), 
                    app.state.orders_df, 
                    app.state.order_products_prior_df
                )
                
                if features_df.empty:
                    logger.warning(f"No features generated for demo user {request.user_id}")
                    return {
                        "user_id": request.user_id,
                        "predicted_products": [],
                        "source": "demo_csv",
                        "feature_engineering": "unified",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": "No order history found in demo data"
                    }
                
                # Generate prediction
                predicted_product_ids = app.state.model.predict(features_df, int(instacart_user_id))
                
                return {
                    "user_id": request.user_id,
                    "predicted_products": predicted_product_ids,
                    "source": "demo_csv",
                    "feature_engineering": "unified",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Regular user - use database prediction
                predictions = app.state.prediction_service.predict_next_basket(request.user_id)
                
                return {
                    "user_id": request.user_id,
                    "predicted_products": predictions,
                    "source": "database",
                    "feature_engineering": "unified",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database prediction failed for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# ============================================================================
# DEMAND 3: CONSOLIDATED PREDICTION COMPARISON ENDPOINT
# ============================================================================

@app.post("/demo/prediction-comparison/{user_id_str}", tags=["Demo"])
async def get_demo_prediction_comparison(user_id_str: str):
    """
    DEMAND 3: Consolidated endpoint - prediction + ground truth + metrics in single call.
    Uses CSV data only, no database interaction.
    """
    try:
        user_id = int(user_id_str)
        
        # Validate model and data availability
        if not app.state.model:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        if app.state.data_loaded.get("orders", 0) == 0:
            raise HTTPException(status_code=503, detail="CSV data not available")
        
        logger.info(f"Generating consolidated prediction comparison for user {user_id}")
        
        # STEP 1: Generate prediction from CSV data
        order_history = _generate_order_history_from_csv(user_id)
        if not order_history:
            raise HTTPException(
                status_code=404, 
                detail=f"No order history found for user {user_id} in CSV data. Try user IDs: 1, 7, 13, 25, 31, 42, 55, 60, 78, 92"
            )
        
        # Use DatabaseFeatureEngineer's CSV-compatible method
        features_df = app.state.demo_feature_engineer.generate_features_from_csv_data(
            str(user_id), app.state.orders_df, app.state.order_products_prior_df
        )
        
        if features_df.empty:
            raise HTTPException(status_code=404, detail=f"No features could be generated for demo user {user_id}")
        
        # Generate prediction using the model
        predicted_product_ids = app.state.model.predict(features_df, user_id)
        
        # STEP 2: Get ground truth basket from processed CSV
        user_future = app.state.instacart_future_df[app.state.instacart_future_df['user_id'] == user_id]
        
        if user_future.empty:
            raise HTTPException(status_code=404, detail=f"No ground truth future basket found for user {user_id}")
        
        # Extract ground truth product IDs
        true_product_ids = []
        for _, row in user_future.iterrows():
            if pd.notna(row['products']) and row['products']:
                # Handle both string and list formats
                if isinstance(row['products'], str):
                    try:
                        products = eval(row['products']) if row['products'].startswith('[') else [int(row['products'])]
                    except:
                        products = [int(row['products'])]
                else:
                    products = row['products'] if isinstance(row['products'], list) else [row['products']]
                true_product_ids.extend(products)
        
        # STEP 3: Calculate comparison metrics
        predicted_set = set(predicted_product_ids)
        true_set = set(true_product_ids)
        common_items = predicted_set & true_set
        
        # Enrich with product details
        predicted_products = _get_product_details(list(predicted_set))
        true_products = _get_product_details(list(true_set))
        
        # Return consolidated response
        return {
            "user_id": user_id,
            "predicted_basket": predicted_products,
            "true_future_basket": true_products,
            "comparison_metrics": {
                "predicted_count": len(predicted_set),
                "actual_count": len(true_set),
                "common_items": len(common_items),
                "precision": len(common_items) / len(predicted_set) if predicted_set else 0,
                "recall": len(common_items) / len(true_set) if true_set else 0,
                "f1_score": 2 * len(common_items) / (len(predicted_set) + len(true_set)) if (predicted_set or true_set) else 0
            },
            "order_history_summary": {
                "total_orders": len(order_history),
                "unique_products": len(set(p for order in order_history for p in order['products'])),
                "last_order_date": order_history[-1]['order_date'] if order_history else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo prediction comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

# ============================================================================
# DEMAND 2: MODEL EVALUATION ENDPOINT
# ============================================================================

@app.post("/evaluate-model", tags=["Evaluation"])
async def evaluate_model(sample_size: Optional[int] = Query(None, description="Number of users to evaluate")):
    """
    DEMAND 2: Trigger model evaluation across test set.
    Returns performance metrics for the ML model.
    """
    if not app.state.model:
        raise HTTPException(status_code=503, detail="Model not available for evaluation")
    
    try:
        effective_sample_size = sample_size or EVALUATION_SAMPLE_SIZE
        logger.info(f"Starting model evaluation with sample size: {effective_sample_size}")
        
        evaluator = BasketPredictionEvaluator(
            model=app.state.model,
            feature_engineer=app.state.demo_feature_engineer,
            processed_data_path=PROCESSED_DATA_PATH
        )
        
        metrics = evaluator.evaluate_model(app.state.orders_df, app.state.order_products_prior_df)
        
        return {
            "status": "completed",
            "metrics": metrics,
            "sample_size": effective_sample_size,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# ============================================================================
# DEMO DATA ENDPOINTS
# ============================================================================

@app.get("/demo-data/available-users", tags=["Demo"])
async def get_available_demo_users(limit: int = 100):
    """Get list of available demo user IDs from CSV data."""
    if app.state.data_loaded.get("orders", 0) == 0:
        raise HTTPException(status_code=503, detail="CSV data not loaded")
    
    user_ids = app.state.orders_df['user_id'].unique()[:limit].tolist()
    return {
        "available_users": user_ids,
        "total_count": len(app.state.orders_df['user_id'].unique()),
        "sample_users": [1, 7, 13, 25, 31, 42, 55, 60, 78, 92]  # Known good examples
    }

@app.get("/demo-data/instacart-user-order-history/{user_id}", tags=["Demo"])
async def get_instacart_user_order_history(user_id: int):
    """
    Get order history for a specific Instacart user from CSV data.
    Used by backend to seed demo users.
    """
    if app.state.data_loaded.get("orders", 0) == 0:
        raise HTTPException(status_code=503, detail="CSV data not loaded")
    
    order_history = _generate_order_history_from_csv(user_id)
    
    if not order_history:
        raise HTTPException(
            status_code=404,
            detail=f"No order history found for user {user_id}. Try: 1, 7, 13, 25, 31, 42, 55, 60, 78, 92"
        )
    
    return {
        "user_id": user_id,
        "orders": order_history,
        "summary": {
            "total_orders": len(order_history),
            "unique_products": len(set(p for order in order_history for p in order['products'])),
            "date_range": {
                "first_order": order_history[0]['order_date'] if order_history else None,
                "last_order": order_history[-1]['order_date'] if order_history else None
            }
        }
    }

@app.get("/demo-data/user-stats/{user_id}", tags=["Demo"])
async def get_user_stats(user_id: int):
    """Get detailed statistics for a demo user."""
    if app.state.data_loaded.get("orders", 0) == 0:
        raise HTTPException(status_code=503, detail="CSV data not loaded")
    
    user_orders = app.state.orders_df[app.state.orders_df['user_id'] == user_id]
    
    if user_orders.empty:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in demo data")
    
    # Get order products
    order_ids = user_orders['order_id'].tolist()
    user_products = app.state.order_products_prior_df[
        app.state.order_products_prior_df['order_id'].isin(order_ids)
    ]
    
    # Calculate statistics
    product_counts = user_products['product_id'].value_counts()
    
    return {
        "user_id": user_id,
        "total_orders": len(user_orders),
        "total_products_ordered": len(user_products),
        "unique_products": len(product_counts),
        "avg_products_per_order": len(user_products) / len(user_orders) if len(user_orders) > 0 else 0,
        "top_products": product_counts.head(10).to_dict(),
        "order_frequency": {
            "avg_days_between_orders": user_orders['days_since_prior_order'].mean() if 'days_since_prior_order' in user_orders else None,
            "favorite_day_of_week": int(user_orders['order_dow'].mode()[0]) if not user_orders['order_dow'].empty else None,
            "favorite_hour": int(user_orders['order_hour_of_day'].mode()[0]) if not user_orders['order_hour_of_day'].empty else None
        }
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_order_history_from_csv(user_id: int) -> List[Dict]:
    """Generate order history from CSV data for a specific user."""
    user_orders = app.state.orders_df[app.state.orders_df['user_id'] == user_id].sort_values('order_number')
    
    if user_orders.empty:
        return []
    
    order_history = []
    for _, order in user_orders.iterrows():
        # Get products for this order
        order_products = app.state.order_products_prior_df[
            app.state.order_products_prior_df['order_id'] == order['order_id']
        ]
        
        if not order_products.empty:
            products = order_products['product_id'].tolist()
            
            # Create synthetic date based on order number
            days_offset = int(order['order_number']) * 7
            order_date = datetime.utcnow() - pd.Timedelta(days=180 - days_offset)
            
            order_data = {
                'order_id': str(order['order_id']),
                'order_number': int(order['order_number']),
                'order_date': order_date.isoformat(),
                'order_dow': int(order['order_dow']),
                'order_hour': int(order['order_hour_of_day']),
                'products': products,
                'product_count': len(products)
            }
            order_history.append(order_data)
    
    return order_history

def _get_product_details(product_ids: List[int]) -> List[Dict]:
    """Get product details from CSV data."""
    product_details = []
    
    for pid in product_ids:
        product = app.state.products_df[app.state.products_df['product_id'] == pid]
        if not product.empty:
            product_row = product.iloc[0]
            product_details.append({
                'product_id': int(pid),
                'product_name': product_row['product_name'],
                'aisle_id': int(product_row['aisle_id']) if pd.notna(product_row['aisle_id']) else None,
                'department_id': int(product_row['department_id']) if pd.notna(product_row['department_id']) else None
            })
        else:
            product_details.append({
                'product_id': int(pid),
                'product_name': f'Product {pid}',
                'aisle_id': None,
                'department_id': None
            })
    
    return product_details

# ============================================================================
# RUN THE SERVICE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)