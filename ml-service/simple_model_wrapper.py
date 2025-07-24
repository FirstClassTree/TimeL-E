"""
Simple Model Wrapper for TimeL-E ML Service
Fixed version with robust fallback predictions for demo users.
"""

import os
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SimpleStackedBasketModel:
    """
    Simple wrapper around the stacked basket prediction models.
    Provides robust fallback predictions when models fail to load.
    """
    
    def __init__(self):
        self.stage1_model = None
        self.stage2_model = None
        self.model_loaded = False
        self.model_path = None
        
    def load_models(self, model_path: str = "/app/models") -> bool:
        """
        Load the trained models from the specified path.
        
        Args:
            model_path: Path to directory containing model files
            
        Returns:
            bool: True if models loaded successfully, False otherwise
        """
        self.model_path = model_path
        
        try:
            # Define model file paths
            stage1_path = os.path.join(model_path, "stage1_lgbm.pkl")
            stage2_path = os.path.join(model_path, "stage2_gbc.pkl")
            
            # Check if model files exist
            if not os.path.exists(stage1_path):
                logger.warning(f"Stage 1 model not found at {stage1_path}")
                return False
                
            if not os.path.exists(stage2_path):
                logger.warning(f"Stage 2 model not found at {stage2_path}")
                return False
            
            # Load models
            with open(stage1_path, 'rb') as f:
                self.stage1_model = pickle.load(f)
                
            with open(stage2_path, 'rb') as f:
                self.stage2_model = pickle.load(f)
                
            self.model_loaded = True
            logger.info(f"✅ Models loaded successfully from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.model_loaded = False
            return False
    
    def predict(self, features_df: pd.DataFrame, user_id: Optional[int] = None, top_k: int = 10) -> List[int]:
        """
        Generate basket predictions for a user with robust fallbacks.
        
        Args:
            features_df: DataFrame with user features
            user_id: User ID (for logging purposes)
            top_k: Number of products to recommend
            
        Returns:
            List of predicted product IDs
        """
        # If models are loaded, try to use them
        if self.model_loaded:
            try:
                # Stage 1: Candidate generation (get potential products)
                if hasattr(self.stage1_model, 'predict_proba'):
                    stage1_probs = self.stage1_model.predict_proba(features_df)
                    # Get top candidates from stage 1
                    if stage1_probs.shape[1] > 1:
                        candidate_scores = stage1_probs[:, 1]  # Probability of class 1
                    else:
                        candidate_scores = stage1_probs[:, 0]
                else:
                    candidate_scores = self.stage1_model.predict(features_df)
                
                # Stage 2: Refine predictions using stage 2 model
                if hasattr(self.stage2_model, 'predict_proba'):
                    stage2_probs = self.stage2_model.predict_proba(features_df)
                    if stage2_probs.shape[1] > 1:
                        final_scores = stage2_probs[:, 1]
                    else:
                        final_scores = stage2_probs[:, 0]
                else:
                    final_scores = self.stage2_model.predict(features_df)
                
                # Combine scores (simple average)
                if len(candidate_scores) == len(final_scores):
                    combined_scores = (candidate_scores + final_scores) / 2
                else:
                    combined_scores = final_scores
                
                # Convert to product IDs and get top K
                if len(combined_scores) > 0:
                    # Get indices of top scores and map to actual product IDs
                    top_indices = np.argsort(combined_scores)[-top_k:][::-1]
                    predicted_products = [features_df.iloc[idx]['product_id'] for idx in top_indices if idx < len(features_df)]
                    logger.info(f"Generated {len(predicted_products)} ML predictions for user {user_id}")
                    return predicted_products[:top_k]
                    
            except Exception as e:
                logger.warning(f"ML model prediction failed for user {user_id}: {e}, falling back to feature-based prediction")
        
        # Fallback: Feature-based prediction when models fail or aren't loaded
        if not features_df.empty and 'product_id' in features_df.columns:
            try:
                # Use user-product features to make smart recommendations
                feature_scores = features_df.copy()
                
                # Calculate a simple recommendation score based on available features
                if 'up_reorder_ratio' in feature_scores.columns:
                    feature_scores['score'] = feature_scores['up_reorder_ratio']
                elif 'up_orders' in feature_scores.columns:
                    feature_scores['score'] = feature_scores['up_orders'] / feature_scores['user_total_orders']
                else:
                    # Random scoring as last resort
                    feature_scores['score'] = np.random.random(len(feature_scores))
                
                # Get top products by score
                top_products = feature_scores.nlargest(top_k, 'score')['product_id'].tolist()
                logger.info(f"Generated {len(top_products)} feature-based predictions for user {user_id}")
                return top_products
                
            except Exception as e:
                logger.warning(f"Feature-based prediction failed for user {user_id}: {e}")
        
        # Final fallback: Popular products for demo purposes
        popular_products = [24852, 13176, 21137, 21903, 47209, 27845, 22935, 47766, 17122, 26604]  # Real product IDs from dataset
        logger.info(f"Using popular products fallback for user {user_id}")
        return popular_products[:top_k]
    
    def predict_simple(self, user_features: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Simple prediction interface that takes user features as a dictionary.
        
        Args:
            user_features: Dictionary of user features
            top_k: Number of products to recommend
            
        Returns:
            List of dictionaries with product predictions
        """
        try:
            # Convert dict to DataFrame
            features_df = pd.DataFrame([user_features])
            
            # Get predictions
            product_ids = self.predict(features_df, top_k=top_k)
            
            # Format as list of dicts
            predictions = []
            for i, product_id in enumerate(product_ids):
                predictions.append({
                    "product_id": product_id,
                    "rank": i + 1,
                    "score": 1.0 - (i * 0.1)  # Mock decreasing scores
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Simple prediction failed: {e}")
            return []
    
    def is_loaded(self) -> bool:
        """Check if models are loaded."""
        return self.model_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "loaded": self.model_loaded,
            "model_path": self.model_path,
            "stage1_model_type": type(self.stage1_model).__name__ if self.stage1_model else None,
            "stage2_model_type": type(self.stage2_model).__name__ if self.stage2_model else None
        }
