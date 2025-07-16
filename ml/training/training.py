# =====================================================================================
# 1. IMPORTS
# =====================================================================================
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.ensemble import GradientBoostingClassifier
import joblib
import os
import json
import logging
from typing import Dict, Any, List, Tuple

print("✅ Dependencies installed and modules imported.")


# =====================================================================================
# 2. HELPER FUNCTIONS AND CLASSES
# (Self-contained script with optimized class definitions)
# =====================================================================================

# --- Logger Setup ---
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configures a simple logger for the script."""
    logger_instance = logging.getLogger(name)
    if not logger_instance.hasHandlers():
        logger_instance.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger_instance.addHandler(ch)
        logger_instance.propagate = False
    return logger_instance


logger = setup_logger(__name__)


# --- Memory Optimization ---
def optimize_dataframes(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Downcasts numerical columns to more memory-efficient types."""
    logger.info("--- Optimizing DataFrame memory usage ---")
    for name, df in dataframes.items():
        for col in df.columns:
            if df[col].dtype == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
            if df[col].dtype == 'int64':
                df[col] = pd.to_numeric(df[col], downcast='integer')
        logger.info(f"Optimized '{name}' DataFrame.")
    return dataframes


# --- OPTIMIZED Feature Engineering ---
class UnifiedFeatureEngineer:
    """
    Performs feature engineering in a fully vectorized manner for high performance.
    """

    def __init__(self):
        logger.info("UnifiedFeatureEngineer initialized (Vectorized).")

    def generate_all_features(self, orders: pd.DataFrame, order_products: pd.DataFrame) -> pd.DataFrame:
        """
        Generates all user, product, and user-product features at once.
        """
        logger.info("--- Starting vectorized feature generation ---")

        # 1. Product-level features
        logger.info("Step 1/4: Calculating product-level features...")
        prod_features = pd.DataFrame(order_products.groupby('product_id').size(), columns=['prod_order_count'])
        prod_features['prod_reorder_ratio'] = order_products.groupby('product_id')['reordered'].mean()

        # 2. User-level features
        logger.info("Step 2/4: Calculating user-level features...")
        user_features = orders.groupby('user_id').agg(
            user_total_orders=('order_number', 'max'),
            user_avg_days_between_orders=('days_since_prior_order', 'mean'),
            user_std_days_between_orders=('days_since_prior_order', 'std'),
            user_favorite_dow=('order_dow', lambda x: x.mode()[0]),
            user_favorite_hour=('order_hour_of_day', lambda x: x.mode()[0])
        )

        # 3. User-Product level features
        logger.info("Step 3/4: Calculating user-product interaction features...")
        # Merge orders with order_products to get user_id for each product purchase
        up_features_df = order_products.merge(orders, on='order_id', how='left')

        # Calculate number of times a user bought a product and reorder ratio
        up_features = up_features_df.groupby(['user_id', 'product_id']).agg(
            up_orders=('order_id', 'count'),
            up_reorder_count=('reordered', lambda x: x.sum() > 1)
        ).reset_index()

        # Calculate when a user last bought a product
        up_features = up_features.merge(
            up_features_df.groupby(['user_id', 'product_id'])['order_number'].max().reset_index(
                name='up_last_order_num'),
            on=['user_id', 'product_id']
        )
        # Merge with total orders to calculate orders since last purchase
        up_features = up_features.merge(user_features[['user_total_orders']], on='user_id')
        up_features['up_orders_since_last'] = up_features['user_total_orders'] - up_features['up_last_order_num']

        # 4. Combine all features
        logger.info("Step 4/4: Combining all features into final DataFrame...")
        final_df = up_features.merge(user_features.drop(columns=['user_total_orders']), on='user_id')
        final_df = final_df.merge(prod_features, on='product_id')

        # Clean up intermediate columns
        final_df = final_df.drop(columns=['up_last_order_num'])

        logger.info(f"✅ Vectorized feature generation complete. Shape: {final_df.shape}")
        return final_df


# --- Model Classes (Unchanged logic, just wrappers) ---
class CandidateGenerator:
    """Stage 1 Model: LightGBM to generate candidate products."""

    def __init__(self):
        self.params = {
            'objective': 'binary', 'metric': ['binary_logloss', 'auc'], 'boosting_type': 'gbdt',
            'n_estimators': 1000, 'learning_rate': 0.05, 'num_leaves': 512,
            'verbose': -1, 'num_threads': -1, 'random_state': 42
        }
        self.model = lgb.LGBMClassifier(**self.params)
        self.candidate_thresholds = [0.16, 0.20, 0.26]

    def train(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series):
        logger.info("--- Training Stage 1: Candidate Generator (LightGBM) ---")
        self.model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                       eval_metric='logloss', callbacks=[lgb.early_stopping(100, verbose=False)])
        logger.info("--- Stage 1 Training Complete ---")

    def save(self, path=".", filename="stage1_lgbm.pkl"):
        joblib.dump(self.model, os.path.join(path, filename))


class BasketSelector:
    """Stage 2 Model: GradientBoostingClassifier to select the best basket."""

    def __init__(self):
        self.model = GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.05)

    def train(self, X_meta_features: pd.DataFrame, y_best_basket_index: pd.Series):
        logger.info("--- Training Stage 2: Basket Selector (Gradient Boosting) ---")
        self.model.fit(X_meta_features, y_best_basket_index)
        logger.info("--- Stage 2 Training Complete ---")

    def save(self, path=".", filename="stage2_gbc.pkl"):
        joblib.dump(self.model, os.path.join(path, filename))


# --- OPTIMIZED Stacked Model Training ---
class StackedBasketModel:
    """Orchestrates the two-stage model training with optimized data handling."""

    def __init__(self):
        self.stage1_generator = CandidateGenerator()
        self.stage2_selector = BasketSelector()

    def _calculate_f1_vectorized(self, candidates_df: pd.DataFrame, actuals_df: pd.DataFrame) -> pd.Series:
        """Calculates F1 score for each user in a vectorized way."""
        # Merge candidates with actuals to find true positives
        merged = candidates_df.merge(actuals_df, how='left', on=['user_id', 'product_id'], indicator=True)
        tp_counts = merged[merged['_merge'] == 'both'].groupby('user_id').size()

        # Get total predictions and actuals per user
        pred_counts = candidates_df.groupby('user_id').size()
        actual_counts = actuals_df.groupby('user_id').size()

        # Combine into a single dataframe for calculation
        f1_df = pd.DataFrame({'tp': tp_counts, 'pred_count': pred_counts, 'actual_count': actual_counts}).fillna(0)

        precision = f1_df['tp'] / f1_df['pred_count']
        recall = f1_df['tp'] / f1_df['actual_count']

        f1_score = 2 * (precision * recall) / (precision + recall)
        return f1_score.fillna(0)

    def train(self, features_df: pd.DataFrame, future_df: pd.DataFrame, keyset: dict):
        """Main training function with optimized data preparation."""
        train_users, valid_users = keyset['train'], keyset['valid']

        # --- 1. Prepare datasets for Stage 1 ---
        logger.info("--- Preparing datasets for Stage 1 training ---")

        def prepare_dataset(user_ids):
            user_features = features_df[features_df['user_id'].isin(user_ids)]
            # Merge with ground truth 'future' data to create labels
            labels = future_df.merge(user_features[['user_id', 'product_id']], on=['user_id', 'product_id'],
                                     how='right')
            labels['label'] = labels['order_id'].notna().astype(int)
            # Combine features with labels
            data = user_features.merge(labels[['user_id', 'product_id', 'label']], on=['user_id', 'product_id'],
                                       how='left').fillna(0)
            feature_cols = [col for col in data.columns if col not in ['user_id', 'product_id', 'label']]
            return data[feature_cols], data['label'], data[['user_id', 'product_id']]

        X_train, y_train, _ = prepare_dataset(train_users)
        X_val, y_val, _ = prepare_dataset(valid_users)

        # --- 2. Train Stage 1 Model ---
        self.stage1_generator.train(X_train, y_train, X_val, y_val)

        # --- 3. Generate Meta-Features for Stage 2 (Vectorized) ---
        logger.info("--- Generating meta-features for Stage 2 (Vectorized) ---")

        # Get Stage 1 predictions for all training users at once
        train_features_with_ids = features_df[features_df['user_id'].isin(train_users)]
        X_train_stage1, _, _ = prepare_dataset(train_users)
        train_features_with_ids['probability'] = self.stage1_generator.model.predict_proba(X_train_stage1)[:, 1]

        # Get ground truth for training users
        actuals_df = future_df[future_df['user_id'].isin(train_users)][['user_id', 'product_id']]

        meta_features_dfs = []
        f1_scores_by_threshold = {}

        # Generate candidate baskets and meta-features for each threshold
        for i, threshold in enumerate(self.stage1_generator.candidate_thresholds):
            candidates = train_features_with_ids[train_features_with_ids['probability'] > threshold]

            # Calculate meta-features (mean, max, min probability per user)
            meta_df = candidates.groupby('user_id')['probability'].agg(['mean', 'max', 'min']).add_prefix(f'thres{i}_')
            meta_features_dfs.append(meta_df)

            # Calculate F1 scores for this threshold
            f1_scores_by_threshold[f'f1_{i}'] = self._calculate_f1_vectorized(candidates, actuals_df)

        # Combine all meta-features
        X_meta_train = pd.concat(meta_features_dfs, axis=1).fillna(0)

        # Combine all F1 scores and find the index of the best basket for each user
        f1_df = pd.concat(f1_scores_by_threshold, axis=1)
        y_meta_train = f1_df.idxmax(axis=1).str.replace('f1_', '').astype(int)

        # Align training data (some users might not have any predictions)
        X_meta_train, y_meta_train = X_meta_train.align(y_meta_train, join='inner', axis=0)

        # --- 4. Train Stage 2 Model ---
        self.stage2_selector.train(X_meta_train, y_meta_train)

        # --- 5. Save Models ---
        self.save_models()

    def save_models(self, path="."):
        os.makedirs(path, exist_ok=True)
        self.stage1_generator.save(path)
        self.stage2_selector.save(path)
        logger.info(f"--- Models saved to {path} ---")


print("✅ All required classes and functions defined.")

# =====================================================================================
# 3. DATA LOADING AND PREPROCESSING
# =====================================================================================
logger.info("--- Starting Data Loading and Preprocessing ---")

# Load data
data_files = {
    'orders': 'orders.csv',
    'order_products_prior': 'order_products__prior.csv',
    'order_products_train': 'order_products__train.csv',
    'products': 'products.csv',
    'departments': 'departments.csv'
}
data = {name: pd.read_csv(f) for name, f in data_files.items()}

# Optimize memory usage
data = optimize_dataframes(data)

# Combine prior and train order products
data['order_products_combined'] = pd.concat([data['order_products_prior'], data['order_products_train']])

# Get user keysets for train/validation/test split
keyset = {
    'train': data['orders'][data['orders']['eval_set'] == 'train']['user_id'].unique(),
    'valid': data['orders'][data['orders']['eval_set'] == 'train']['user_id'].unique(),
    # Using train for validation is common in Kaggle kernels
    'test': data['orders'][data['orders']['eval_set'] == 'test']['user_id'].unique()
}

# Define the ground truth for what a user will order next
instacart_future_df = data['order_products_train'].merge(data['orders'], on='order_id')[
    ['user_id', 'product_id', 'order_id']]

# Generate features for all users using the optimized, vectorized engineer
feature_engineer = UnifiedFeatureEngineer()
features_df = feature_engineer.generate_all_features(data['orders'], data['order_products_combined'])

logger.info(f"✅ Preprocessing complete. Features generated for {features_df['user_id'].nunique()} users.")
print(f"Features DataFrame shape: {features_df.shape}")

# =====================================================================================
# 4. SAVE INTERMEDIATE ARTIFACTS
# =====================================================================================

logger.info("--- Saving intermediate training artifacts ---")

# Save the processed features DataFrame to CSV
features_df.to_csv('features_df.csv', index=False)
print("✅ Processed features saved to features_df.csv")

# Save the train/validation/test user ID keysets to JSON
keyset_to_save = {k: v.tolist() for k, v in keyset.items()}
with open('keyset.json', 'w') as f:
    json.dump(keyset_to_save, f)
print("✅ Keyset saved to keyset.json")

# =====================================================================================
# 5. MODEL TRAINING
# =====================================================================================
logger.info("--- Initializing the Stacked Model for Training ---")
stacked_model = StackedBasketModel()

# Train the model using the optimized training pipeline
stacked_model.train(features_df, instacart_future_df, keyset)

print("\n🎉🎉🎉 MODEL TRAINING COMPLETE! 🎉🎉🎉")
print("You can now download 'stage1_lgbm.pkl' and 'stage2_gbc.pkl' from the file explorer.")