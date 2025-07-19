# ml-service/src/services/prediction_service.py
# COMPLETELY UPDATED: Removed legacy mode, fixed constructor, pure database mode

import pandas as pd
from typing import List, Dict, Optional
from ..models.stacked_basket_model import StackedBasketModel
from ..features.engineering import UnifiedFeatureEngineer as DatabaseFeatureEngineer
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class PredictionService:
    """
    Clean prediction service with direct database access architecture.
    NO LEGACY MODE - app was never deployed.
    """
    
    def __init__(self, model: StackedBasketModel, processed_data_path: str):
        """
        Initialize prediction service with database mode only.
        
        Args:
            model: Trained StackedBasketModel for two-stage prediction
            processed_data_path: Path to processed data for static product features
        """
        if not model:
            raise ValueError("PredictionService requires a valid trained model")
        
        self.model = model
        self.processed_data_path = processed_data_path
        
        # Initialize feature engineering with database access
        self.feature_engineer = DatabaseFeatureEngineer(processed_data_path)
        logger.info("PredictionService initialized with DATABASE mode")
    
    def predict_next_basket(self, user_id: str) -> List[int]:
        """
        Main prediction method - DATABASE MODE ONLY.
        
        Args:
            user_id: User identifier for database lookup
            
        Returns:
            List of predicted product IDs from StackedBasketModel
        """
        logger.info(f"Starting prediction for user_id: {user_id}")
        
        try:
            # Generate features using feature engineering
            features_df = self.feature_engineer.generate_features_from_database(user_id)
            
            if features_df.empty:
                logger.warning(f"No features generated for user {user_id}")
                return []
            
            # REAL PREDICTION: Two-stage StackedBasketModel
            # Stage 1: LightGBM CandidateGenerator → 3 candidate baskets + meta-features
            # Stage 2: GradientBoostingClassifier BasketSelector → selects best basket
            predicted_product_ids = self.model.predict(features_df, user_id)
            
            logger.info(f"Generated {len(predicted_product_ids)} predictions for user {user_id}")
            return predicted_product_ids
            
        except Exception as e:
            logger.error(f"Prediction failed for user {user_id}: {e}", exc_info=True)
            return []
    
    def predict_for_user(self, user_id: str) -> List[int]:
        """
        Alias for predict_next_basket for API compatibility.
        """
        return self.predict_next_basket(user_id)
    
    def get_service_info(self) -> Dict[str, any]:
        """Get information about the prediction service configuration."""
        return {
            "mode": "database_only",
            "feature_engineering": "black_box", 
            "architecture": "direct_database_access",
            "model_type": "StackedBasketModel",
            "stages": ["LightGBM_CandidateGenerator", "GradientBoostingClassifier_BasketSelector"],
            "legacy_mode": False
        }


class EnhancedPredictionService(PredictionService):
    """
    Enhanced prediction service with monitoring capabilities.
    Extends base PredictionService with performance tracking.
    """
    
    def __init__(self, model: StackedBasketModel, processed_data_path: str):
        """Initialize enhanced service with monitoring."""
        super().__init__(model, processed_data_path)
        self.prediction_count = 0
        self.successful_predictions = 0
        logger.info("EnhancedPredictionService initialized with monitoring")
    
    def predict_next_basket(self, user_id: str) -> List[int]:
        """Enhanced prediction with monitoring."""
        self.prediction_count += 1
        
        try:
            result = super().predict_next_basket(user_id)
            if result:
                self.successful_predictions += 1
            return result
        except Exception as e:
            logger.error(f"Enhanced prediction failed for user {user_id}: {e}")
            return []
    
    def get_service_stats(self) -> Dict[str, any]:
        """Get service statistics with monitoring data."""
        success_rate = (self.successful_predictions / self.prediction_count) if self.prediction_count > 0 else 0
        
        return {
            **self.get_service_info(),
            "total_predictions": self.prediction_count,
            "successful_predictions": self.successful_predictions,
            "success_rate": success_rate,
            "monitoring_enabled": True
        }