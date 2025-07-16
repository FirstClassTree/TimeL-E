# ml-service/src/models/stacked_basket_model.py

import pandas as pd
import numpy as np
import os
import logging
from typing import List, Tuple

from .stage1_candidate_generator import CandidateGenerator
from .stage2_basket_selector import BasketSelector

logger = logging.getLogger(__name__)

class StackedBasketModel:
    """
    Orchestrates the two-stage stacked model for training and prediction.
    This class assumes that the complex data preparation and meta-feature
    generation are handled by the calling script (e.g., training.py).
    """
    def __init__(self):
        self.stage1_generator = CandidateGenerator()
        self.stage2_selector = BasketSelector()

    def train(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series,
              X_meta_train: pd.DataFrame, y_meta_train: pd.Series):
        """
        Trains both stages of the model.

        Args:
            X_train, y_train: Training data for Stage 1.
            X_val, y_val: Validation data for Stage 1.
            X_meta_train: Meta-features for training Stage 2.
            y_meta_train: Target labels (best basket index) for Stage 2.
        """
        # Train Stage 1
        self.stage1_generator.train(X_train, y_train, X_val, y_val)
        
        # Train Stage 2
        self.stage2_selector.train(X_meta_train, y_meta_train)

        # Save both models
        self.save_models()

    def predict(self, features_df: pd.DataFrame) -> List[int]:
        """
        The main prediction function to be called by the API. It performs the
        full two-stage prediction.

        Args:
            features_df: The fully engineered feature DataFrame for a single user.

        Returns:
            A list of predicted product IDs.
        """
        if features_df.empty:
            logger.warning("Prediction attempted with an empty feature DataFrame.")
            return []

        # --- Stage 1: Generate product probabilities ---
        feature_cols = [col for col in features_df.columns if col not in ['user_id', 'product_id']]
        probabilities = self.stage1_generator.predict_proba(features_df[feature_cols])
        
        prob_df = features_df[['product_id']].copy()
        prob_df['probability'] = probabilities
        
        # --- Generate candidate baskets and meta-features ---
        candidate_baskets = []
        meta_features_list = []
        for i, threshold in enumerate(self.stage1_generator.candidate_thresholds):
            basket_df = prob_df[prob_df['probability'] > threshold]
            candidate_baskets.append(basket_df)
            
            meta_features = {}
            if not basket_df.empty:
                meta_features[f'thres{i}_mean'] = basket_df['probability'].mean()
                meta_features[f'thres{i}_max'] = basket_df['probability'].max()
                meta_features[f'thres{i}_min'] = basket_df['probability'].min()
            else:
                meta_features[f'thres{i}_mean'] = 0
                meta_features[f'thres{i}_max'] = 0
                meta_features[f'thres{i}_min'] = 0
            meta_features_list.append(meta_features)
            
        final_meta_features = {k: v for d in meta_features_list for k, v in d.items()}
        meta_features_df = pd.DataFrame([final_meta_features])
        
        # --- Stage 2: Select the best basket ---
        best_basket_index = self.stage2_selector.predict(meta_features_df)
        
        # Return the chosen basket's product IDs
        final_basket = candidate_baskets[best_basket_index]['product_id'].tolist()
        
        return final_basket

    def save_models(self, path: str = "."):
        """Saves both stage models to the specified path."""
        os.makedirs(path, exist_ok=True)
        self.stage1_generator.save(path)
        self.stage2_selector.save(path)
        logger.info(f"--- All models saved to {path} ---")

    def load_models(self, path: str):
        """Loads both stage models from the specified path."""
        self.stage1_generator.load(os.path.join(path, "stage1_lgbm.pkl"))
        self.stage2_selector.load(os.path.join(path, "stage2_gbc.pkl"))
        logger.info("--- Both Stage 1 and Stage 2 models loaded successfully ---")