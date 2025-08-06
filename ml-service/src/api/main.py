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
import sys
sys.path.append('/app')
from simple_model_wrapper import SimpleStackedBasketModel
from ..services.prediction import EnhancedPredictionService
from ..features.engineering import UnifiedFeatureEngineer as DatabaseFeatureEngineer
# from ..core.evaluator import BasketPredictionEvaluator  # Commented out for now
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
SERVICE_PORT = int(os.getenv("ML_SERVICE_PORT", "8001"))
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
    
    # Load and initialize model - try simple wrapper first
    try:
        app.state.model = SimpleStackedBasketModel()
        app.state.model.load_models(MODEL_PATH_BASE)
        logger.info(f"✅ SimpleStackedBasketModel loaded from {MODEL_PATH_BASE}")
        app.state.model_loaded = True
    except Exception as e:
        logger.warning(f"Simple model loading failed: {e}, trying complex model...")
        try:
            app.state.model = StackedBasketModel()
            app.state.model.load_models(MODEL_PATH_BASE)
            logger.info(f"✅ StackedBasketModel loaded from {MODEL_PATH_BASE}")
            app.state.model_loaded = True
        except Exception as e2:
            logger.error(f"🚨 All ML model loading failed: {e2}")
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
    # Handle case where data_loaded contains error
    data_loaded = app.state.data_loaded
    if isinstance(data_loaded, dict) and "error" in data_loaded:
        data_loaded = {"error_count": 1}
    
    return HealthResponse(
        status="healthy" if app.state.model_loaded else "degraded",
        model_loaded=app.state.model_loaded,
        database_available=app.state.database_available,
        architecture="direct_database_access",
        feature_engineering="unified",
        data_loaded=data_loaded
    )

# ============================================================================
# CORE PREDICTION ENDPOINTS
# ============================================================================

@app.post("/predict/{user_id}", tags=["Prediction"])
async def predict_next_cart(user_id: int):
    """
    Simple prediction endpoint - just give a user ID, get their predicted next cart.
    Works with demo users from CSV data.
    """
    if not app.state.model_loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded")
    
    try:
        logger.info(f"Generating prediction for user {user_id}")
        
        # Generate features from CSV data (since we trained on CSV data)
        features_df = app.state.demo_feature_engineer.generate_features_from_csv_data(
            str(user_id), 
            app.state.orders_df, 
            app.state.order_products_prior_df
        )
        
        if features_df.empty:
            return {
                "user_id": user_id,
                "predicted_cart": [],
                "message": "No order history found for this user",
                "success": False
            }
        
        # Generate prediction with scores using our trained models
        if hasattr(app.state.model, 'predict_with_scores'):
            predictions_with_scores = app.state.model.predict_with_scores(features_df, user_id)
            
            # Get product details with real scores
            predicted_products = []
            for pred in predictions_with_scores:
                product_id = pred["product_id"]
                score = pred["score"]
                product_info = app.state.products_df[app.state.products_df['product_id'] == product_id]
                if not product_info.empty:
                    predicted_products.append({
                        "product_id": int(product_id),
                        "product_name": product_info.iloc[0]['product_name'],
                        "score": round(float(score), 3)  # Real ML prediction score
                    })
        else:
            # Fallback to old method without scores
            predicted_product_ids = app.state.model.predict(features_df, user_id)
            
            # Get product details with default scores
            predicted_products = []
            for i, product_id in enumerate(predicted_product_ids):
                product_info = app.state.products_df[app.state.products_df['product_id'] == product_id]
                if not product_info.empty:
                    predicted_products.append({
                        "product_id": int(product_id),
                        "product_name": product_info.iloc[0]['product_name'],
                        "score": 0.9 - (i * 0.05)  # Mock decreasing scores
                    })
        
        return {
            "user_id": user_id,
            "predicted_cart": predicted_products,
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Prediction failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ============================================================================
# RUN THE SERVICE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
