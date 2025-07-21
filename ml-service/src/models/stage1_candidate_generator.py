# ml-service/src/models/stage1_candidate_generator.py

import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class CandidateGenerator:
    """
    Stage 1 Model: Uses LightGBM to generate candidate product probabilities.
    The thresholds for creating baskets are applied in the StackedBasketModel.
    """
    def __init__(self):
        self.params = {
            'objective': 'binary',
            'metric': ['binary_logloss', 'auc'],
            'boosting_type': 'gbdt',
            'n_estimators': 1000,
            'learning_rate': 0.05,
            'num_leaves': 512,
            'verbose': -1,
            'num_threads': -1,
            'random_state': 42
        }
        self.model = lgb.LGBMClassifier(**self.params)
        # Thresholds are managed by the parent model but defined here for reference
        self.candidate_thresholds = [0.16, 0.20, 0.26]

    def train(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series):
        """Trains the LightGBM model with early stopping."""
        logger.info("--- Training Stage 1: Candidate Generator (LightGBM) ---")
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            eval_metric='logloss',
            callbacks=[lgb.early_stopping(100, verbose=False)]
        )
        logger.info("--- Stage 1 Training Complete ---")

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts the reorder probability for each product."""
        if X.empty:
            return np.array([])
        return self.model.predict_proba(X)[:, 1]

    def save(self, path: str = ".", filename: str = "stage1_lgbm.pkl"):
        """Saves the trained model to a file."""
        os.makedirs(path, exist_ok=True)
        joblib.dump(self.model, os.path.join(path, filename))
        logger.info(f"Stage 1 model saved to {os.path.join(path, filename)}")

    def load(self, path: str):
        """Loads a trained model from a file."""
        self.model = joblib.load(path)
        logger.info(f"Stage 1 model loaded from {path}")
