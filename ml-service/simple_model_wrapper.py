#!/usr/bin/env python3
"""
Simple Model Wrapper for Quick-Trained Models
Provides compatibility between our simple LightGBM/GradientBoosting models
and the expected StackedBasketModel interface.
"""

import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class SimpleStackedBasketModel:
    """
    Simplified version of StackedBasketModel that works with our quick-trained models.
    """
    
    def __init__(self):
        self.stage1_model = None
        self.stage2_model = None
        self.thresholds = [0.2, 0.3, 0.4]  # Default thresholds
        
    def load_models(self, path: str):
        """Load the simple trained models."""
        try:
            self.stage1_model = joblib.load(os.path.join(path, "stage1_lgbm.pkl"))
            self.stage2_model = joblib.load(os.path.join(path, "stage2_gbc.pkl"))
            logger.info("✅ Simple models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load simple models: {e}")
            raise
    
    def predict(self, features_df: pd.DataFrame, user_id: int = None) -> List[int]:
        """
        Generate predictions using our simple models.
        """
        if features_df.empty:
            logger.warning("Empty features DataFrame")
            return []
            
        if self.stage1_model is None:
            logger.error("Models not loaded")
            return []
        
        try:
            # Use only the 3 features our model was trained on
            expected_features = ['order_count', 'reorder_sum', 'reorder_rate']
            
            # Check if we have the expected features
            available_features = [col for col in expected_features if col in features_df.columns]
            
            if len(available_features) < 3:
                logger.warning(f"Missing expected features. Available: {available_features}, Expected: {expected_features}")
                # Fallback: use any numeric columns if expected ones aren't available
                feature_cols = [col for col in features_df.columns if col not in ['user_id', 'product_id']][:3]
                if len(feature_cols) < 3:
                    logger.error("Not enough features available")
                    return []
            else:
                feature_cols = available_features
            
            # Get product IDs
            if 'product_id' not in features_df.columns:
                logger.warning("No product_id column found")
                return []
                
            product_ids = features_df['product_id'].tolist()
            
            # Stage 1: Get probabilities
            X = features_df[feature_cols].fillna(0)
            probabilities = self.stage1_model.predict_proba(X)[:, 1]  # Get positive class probabilities
            
            # Create candidates for each threshold
            candidates = []
            meta_features = []
            
            for threshold in self.thresholds:
                # Get products above threshold
                mask = probabilities > threshold
                candidate_products = [product_ids[i] for i in range(len(product_ids)) if mask[i]]
                candidates.append(candidate_products)
                
                # Calculate meta-features for this threshold
                if np.any(mask):
                    threshold_probs = probabilities[mask]
                    meta_features.extend([
                        threshold_probs.mean(),
                        threshold_probs.max(), 
                        threshold_probs.min()
                    ])
                else:
                    meta_features.extend([0.0, 0.0, 0.0])
            
            # Stage 2: Select best basket
            if len(meta_features) > 0:
                meta_X = np.array(meta_features).reshape(1, -1)
                best_threshold_idx = self.stage2_model.predict(meta_X)[0]
                
                # Ensure index is valid
                best_threshold_idx = max(0, min(best_threshold_idx, len(candidates) - 1))
                
                return candidates[best_threshold_idx]
            else:
                # Fallback: return products with probability > 0.3
                mask = probabilities > 0.3
                return [product_ids[i] for i in range(len(product_ids)) if mask[i]]
                
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Fallback: return top 5 products by probability
            try:
                feature_cols = [col for col in features_df.columns if col not in ['user_id', 'product_id']]
                X = features_df[feature_cols].fillna(0)
                probabilities = self.stage1_model.predict_proba(X)[:, 1]
                top_indices = np.argsort(probabilities)[-5:]  # Top 5
                return [features_df.iloc[i]['product_id'] for i in top_indices if 'product_id' in features_df.columns]
            except:
                return []
