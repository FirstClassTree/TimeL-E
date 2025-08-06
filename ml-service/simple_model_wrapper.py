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
        Generate basket predictions for a user using trained models.
        
        Args:
            features_df: DataFrame with user features
            user_id: User ID (for logging purposes)
            top_k: Number of products to recommend
            
        Returns:
            List of predicted product IDs
        """
        # If models are loaded, use them for real ML predictions
        if self.model_loaded and self.stage1_model is not None:
            try:
                logger.info(f"Using trained ML models for user {user_id}")
                
                # Prepare features for prediction (exclude non-feature columns)
                feature_cols = [col for col in features_df.columns 
                               if col not in ['user_id', 'product_id']]
                X_features = features_df[feature_cols]
                
                # Stage 1: Candidate generation with LightGBM
                stage1_probs = self.stage1_model.predict_proba(X_features)
                if stage1_probs.shape[1] > 1:
                    candidate_scores = stage1_probs[:, 1]  # Probability of positive class
                else:
                    candidate_scores = stage1_probs[:, 0]
                
                # Add scores to features dataframe
                features_with_scores = features_df.copy()
                features_with_scores['stage1_score'] = candidate_scores
                
                # Sort by stage1 scores and get top candidates (more than top_k for stage 2)
                top_candidates = features_with_scores.nlargest(min(50, len(features_df)), 'stage1_score')
                
                # Stage 2: Use Gradient Boosting for final selection (if we have stage2 model)
                if self.stage2_model is not None and len(top_candidates) > 0:
                    # Create meta-features for stage 2
                    stage2_features = top_candidates[feature_cols]
                    
                    if hasattr(self.stage2_model, 'predict_proba'):
                        stage2_probs = self.stage2_model.predict_proba(stage2_features)
                        if stage2_probs.shape[1] > 1:
                            stage2_scores = stage2_probs[:, 1]
                        else:
                            stage2_scores = stage2_probs[:, 0]
                    else:
                        stage2_scores = self.stage2_model.predict(stage2_features)
                    
                    # Combine stage1 and stage2 scores
                    top_candidates['final_score'] = (top_candidates['stage1_score'] + stage2_scores) / 2
                    final_predictions = top_candidates.nlargest(top_k, 'final_score')
                else:
                    # Use only stage 1 if stage 2 not available
                    final_predictions = top_candidates.head(top_k)
                    final_predictions['final_score'] = final_predictions['stage1_score']
                
                # Extract product IDs
                predicted_product_ids = final_predictions['product_id'].tolist()
                logger.info(f"Generated {len(predicted_product_ids)} real ML predictions for user {user_id}")
                return predicted_product_ids
                
            except Exception as e:
                logger.error(f"ML model prediction failed for user {user_id}: {e}", exc_info=True)
                # Fall through to feature-based prediction
        
        # Fallback: Feature-based prediction when models fail or aren't loaded
        if not features_df.empty and 'product_id' in features_df.columns:
            try:
                logger.info(f"Using feature-based prediction for user {user_id}")
                feature_scores = features_df.copy()
                
                # Calculate a recommendation score based on available features
                if 'up_reorder_ratio' in feature_scores.columns:
                    feature_scores['score'] = feature_scores['up_reorder_ratio']
                elif 'up_orders' in feature_scores.columns and 'user_total_orders' in feature_scores.columns:
                    feature_scores['score'] = feature_scores['up_orders'] / (feature_scores['user_total_orders'] + 1)
                else:
                    # Use product order count if available
                    if 'prod_order_count' in feature_scores.columns:
                        feature_scores['score'] = feature_scores['prod_order_count'] / feature_scores['prod_order_count'].max()
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
        popular_products = [24852, 13176, 21137, 21903, 47209, 27845, 22935, 47766, 17122, 26604]
        logger.info(f"Using popular products fallback for user {user_id}")
        return popular_products[:top_k]
    
    def predict_with_scores(self, features_df: pd.DataFrame, user_id: Optional[int] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Generate predictions with actual probability scores.
        
        Args:
            features_df: DataFrame with user features
            user_id: User ID (for logging purposes)
            top_k: Number of products to recommend
            
        Returns:
            List of dicts with product_id and score
        """
        # If models are loaded, use them for real ML predictions with scores
        if self.model_loaded and self.stage1_model is not None:
            try:
                logger.info(f"Generating scored predictions for user {user_id}")
                
                # Prepare features for prediction
                feature_cols = [col for col in features_df.columns 
                               if col not in ['user_id', 'product_id']]
                X_features = features_df[feature_cols]
                
                # Stage 1: Get probabilities
                stage1_probs = self.stage1_model.predict_proba(X_features)
                if stage1_probs.shape[1] > 1:
                    candidate_scores = stage1_probs[:, 1]
                else:
                    candidate_scores = stage1_probs[:, 0]
                
                # Add scores to dataframe
                features_with_scores = features_df.copy()
                features_with_scores['stage1_score'] = candidate_scores
                
                # Get top candidates
                top_candidates = features_with_scores.nlargest(min(50, len(features_df)), 'stage1_score')
                
                # Stage 2: Refine scores if available
                if self.stage2_model is not None and len(top_candidates) > 0:
                    stage2_features = top_candidates[feature_cols]
                    
                    if hasattr(self.stage2_model, 'predict_proba'):
                        stage2_probs = self.stage2_model.predict_proba(stage2_features)
                        if stage2_probs.shape[1] > 1:
                            stage2_scores = stage2_probs[:, 1]
                        else:
                            stage2_scores = stage2_probs[:, 0]
                    else:
                        stage2_scores = self.stage2_model.predict(stage2_features)
                    
                    # Combine scores
                    top_candidates['final_score'] = (top_candidates['stage1_score'] + stage2_scores) / 2
                    final_predictions = top_candidates.nlargest(top_k, 'final_score')
                else:
                    final_predictions = top_candidates.head(top_k)
                    final_predictions['final_score'] = final_predictions['stage1_score']
                
                # Format results with real scores
                results = []
                for _, row in final_predictions.iterrows():
                    results.append({
                        "product_id": int(row['product_id']),
                        "score": float(row['final_score'])
                    })
                
                logger.info(f"Generated {len(results)} ML predictions with scores for user {user_id}")
                return results
                
            except Exception as e:
                logger.error(f"Scored prediction failed for user {user_id}: {e}", exc_info=True)
        
        # Fallback: Use feature-based scoring
        if not features_df.empty and 'product_id' in features_df.columns:
            try:
                feature_scores = features_df.copy()
                
                if 'up_reorder_ratio' in feature_scores.columns:
                    feature_scores['score'] = feature_scores['up_reorder_ratio']
                elif 'up_orders' in feature_scores.columns and 'user_total_orders' in feature_scores.columns:
                    feature_scores['score'] = feature_scores['up_orders'] / (feature_scores['user_total_orders'] + 1)
                else:
                    if 'prod_order_count' in feature_scores.columns:
                        max_count = feature_scores['prod_order_count'].max()
                        feature_scores['score'] = feature_scores['prod_order_count'] / max(max_count, 1)
                    else:
                        feature_scores['score'] = np.random.uniform(0.3, 0.9, len(feature_scores))
                
                # Get top products with scores
                top_products = feature_scores.nlargest(top_k, 'score')
                results = []
                for _, row in top_products.iterrows():
                    results.append({
                        "product_id": int(row['product_id']),
                        "score": float(row['score'])
                    })
                
                logger.info(f"Generated {len(results)} feature-based predictions with scores for user {user_id}")
                return results
                
            except Exception as e:
                logger.warning(f"Feature-based scoring failed for user {user_id}: {e}")
        
        # Final fallback with mock scores
        popular_products = [24852, 13176, 21137, 21903, 47209, 27845, 22935, 47766, 17122, 26604]
        results = []
        for i, product_id in enumerate(popular_products[:top_k]):
            results.append({
                "product_id": product_id,
                "score": 0.9 - (i * 0.05)  # Decreasing scores from 0.9 to 0.45
            })
        
        logger.info(f"Using fallback predictions with mock scores for user {user_id}")
        return results

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
            
            # Get predictions with real scores
            predictions = self.predict_with_scores(features_df, top_k=top_k)
            
            # Add rank information
            for i, pred in enumerate(predictions):
                pred["rank"] = i + 1
            
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
