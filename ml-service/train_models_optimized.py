#!/usr/bin/env python3
"""
OPTIMIZED Training Script with Memory-Efficient Chunked Processing
This version can handle large datasets without memory issues.
"""

import sys
import os
import gc
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.ensemble import GradientBoostingClassifier
import joblib
import json
import logging
from typing import Dict, Any, List, Tuple
from tqdm import tqdm

print("🚀 Starting OPTIMIZED ML Model Training with Chunked Processing...")

# =====================================================================================
# MEMORY AND PROGRESS MONITORING UTILITIES
# =====================================================================================

def log_memory_usage(step_name):
    """Simple memory logging without psutil"""
    print(f"📊 {step_name}: Processing...")

def optimize_dataframe_memory(df, verbose=True):
    """Optimize DataFrame memory usage by downcasting numeric types"""
    if verbose:
        start_mem = df.memory_usage(deep=True).sum() / 1024**2
        print(f"🔧 Memory usage before optimization: {start_mem:.2f} MB")
    
    for col in df.columns:
        col_type = df[col].dtype
        if col_type != object:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float32)
    
    if verbose:
        end_mem = df.memory_usage(deep=True).sum() / 1024**2
        reduction = 100 * (start_mem - end_mem) / start_mem
        print(f"✅ Memory usage after optimization: {end_mem:.2f} MB ({reduction:.1f}% reduction)")
    
    return df

# =====================================================================================
# CHUNKED FEATURE ENGINEERING CLASS
# =====================================================================================

class ChunkedFeatureEngineer:
    """Memory-efficient feature engineering using chunked processing"""
    
    def __init__(self, chunk_size=2000):
        self.chunk_size = chunk_size
        
    def generate_product_features(self, order_products_df):
        """Generate global product features efficiently"""
        print("📊 Step 1/4: Calculating product-level features...")
        log_memory_usage("Before product features")
        
        # Calculate product features in chunks to save memory
        prod_features = order_products_df.groupby('product_id').agg({
            'order_id': 'count',
            'reordered': 'mean'
        }).rename(columns={
            'order_id': 'prod_order_count',
            'reordered': 'prod_reorder_ratio'
        })
        
        prod_features = optimize_dataframe_memory(prod_features, verbose=False)
        log_memory_usage("After product features")
        return prod_features
        
    def generate_user_features(self, orders_df):
        """Generate user-level features efficiently"""
        print("📊 Step 2/4: Calculating user-level features...")
        log_memory_usage("Before user features")
        
        user_features = orders_df.groupby('user_id').agg({
            'order_number': 'max',
            'days_since_prior_order': ['mean', 'std'],
            'order_dow': lambda x: x.mode()[0] if not x.empty else 0,
            'order_hour_of_day': lambda x: x.mode()[0] if not x.empty else 12
        })
        
        # Flatten column names
        user_features.columns = [
            'user_total_orders', 'user_avg_days_between_orders', 
            'user_std_days_between_orders', 'user_favorite_dow', 'user_favorite_hour'
        ]
        
        user_features = optimize_dataframe_memory(user_features, verbose=False)
        log_memory_usage("After user features")
        return user_features
    
    def generate_user_product_features_chunked(self, orders_df, order_products_df, user_ids):
        """Generate user-product features using chunked processing"""
        print("📊 Step 3/4: Calculating user-product features (CHUNKED)...")
        log_memory_usage("Before user-product features")
        
        # Split users into chunks
        user_chunks = [user_ids[i:i + self.chunk_size] for i in range(0, len(user_ids), self.chunk_size)]
        total_chunks = len(user_chunks)
        
        print(f"🔄 Processing {len(user_ids)} users in {total_chunks} chunks of {self.chunk_size}")
        
        all_up_features = []
        
        # Process each chunk
        for chunk_idx, user_chunk in enumerate(tqdm(user_chunks, desc="Processing user chunks")):
            print(f"\n📦 Chunk {chunk_idx + 1}/{total_chunks} - Users {len(user_chunk)}")
            log_memory_usage(f"Chunk {chunk_idx + 1} start")
            
            # Filter orders for current chunk of users
            chunk_orders = orders_df[orders_df['user_id'].isin(user_chunk)]
            
            # Get order products for this chunk
            chunk_order_products = order_products_df.merge(
                chunk_orders[['order_id', 'user_id']], 
                on='order_id', 
                how='inner'
            )
            
            if chunk_order_products.empty:
                continue
                
            # Calculate user-product features for this chunk
            up_features_chunk = chunk_order_products.groupby(['user_id', 'product_id']).agg({
                'order_id': 'count',
                'reordered': 'sum'
            }).rename(columns={
                'order_id': 'up_orders',
                'reordered': 'up_reorder_count'
            }).reset_index()
            
            # Calculate additional features
            user_orders_count = chunk_orders.groupby('user_id')['order_number'].max()
            up_features_chunk = up_features_chunk.merge(
                user_orders_count.rename('user_total_orders'), 
                on='user_id'
            )
            
            up_features_chunk['up_reorder_ratio'] = (
                up_features_chunk['up_reorder_count'] / up_features_chunk['user_total_orders']
            )
            
            # Get last order number for each user-product pair
            last_order_nums = chunk_order_products.groupby(['user_id', 'product_id']).apply(
                lambda x: x.merge(chunk_orders[['order_id', 'order_number']], on='order_id')['order_number'].max()
            ).rename('up_last_order_num')
            
            up_features_chunk = up_features_chunk.merge(
                last_order_nums, 
                on=['user_id', 'product_id']
            )
            
            up_features_chunk['up_orders_since_last'] = (
                up_features_chunk['user_total_orders'] - up_features_chunk['up_last_order_num']
            )
            
            # Clean up
            up_features_chunk = up_features_chunk.drop(['up_last_order_num'], axis=1)
            up_features_chunk = optimize_dataframe_memory(up_features_chunk, verbose=False)
            
            all_up_features.append(up_features_chunk)
            
            # Memory cleanup
            del chunk_orders, chunk_order_products, up_features_chunk
            gc.collect()
            
            log_memory_usage(f"Chunk {chunk_idx + 1} end")
        
        # Combine all chunks
        print("🔗 Combining all chunks...")
        final_up_features = pd.concat(all_up_features, ignore_index=True)
        final_up_features = optimize_dataframe_memory(final_up_features)
        
        log_memory_usage("After user-product features")
        return final_up_features
    
    def generate_all_features_chunked(self, orders_df, order_products_df):
        """Generate all features using chunked processing"""
        print("🏗️ Starting CHUNKED feature generation...")
        
        # Get all unique user IDs
        all_users = orders_df['user_id'].unique()
        print(f"👥 Total users to process: {len(all_users)}")
        
        # Generate global features (these are small)
        prod_features = self.generate_product_features(order_products_df)
        user_features = self.generate_user_features(orders_df)
        
        # Generate user-product features in chunks (this is the memory-intensive part)
        up_features = self.generate_user_product_features_chunked(
            orders_df, order_products_df, all_users
        )
        
        print("📊 Step 4/4: Combining all features...")
        log_memory_usage("Before final combination")
        
        # Merge everything together
        final_features = up_features.merge(user_features, on='user_id', how='left')
        final_features = final_features.merge(prod_features, on='product_id', how='left')
        
        # Fill missing values
        final_features = final_features.fillna(0)
        final_features = optimize_dataframe_memory(final_features)
        
        log_memory_usage("After final combination")
        print(f"✅ Feature generation complete! Final shape: {final_features.shape}")
        
        return final_features

# =====================================================================================
# OPTIMIZED MODEL TRAINING
# =====================================================================================

class OptimizedStackedBasketModel:
    """Optimized training with memory management"""
    
    def __init__(self):
        self.stage1_model = lgb.LGBMClassifier(
            objective='binary', metric=['binary_logloss', 'auc'],
            n_estimators=100, learning_rate=0.05, num_leaves=256,
            verbose=-1, random_state=42
        )
        self.stage2_model = GradientBoostingClassifier(
            n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42
        )
        
    def train_stage1(self, X_train, y_train, X_val, y_val):
        """Train Stage 1 model with memory monitoring"""
        print("🎯 Training Stage 1 (LightGBM)...")
        log_memory_usage("Before Stage 1 training")
        
        self.stage1_model.fit(
            X_train, y_train, 
            eval_set=[(X_val, y_val)],
            eval_metric='logloss',
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )
        
        log_memory_usage("After Stage 1 training")
        print("✅ Stage 1 training complete")
        
    def train_stage2_with_sampling(self, features_df, future_df, train_users, sample_size=10000):
        """Train Stage 2 with user sampling to manage memory"""
        print("🎯 Training Stage 2 (Gradient Boosting) with sampling...")
        log_memory_usage("Before Stage 2 training")
        
        # Sample users if too many
        if len(train_users) > sample_size:
            sampled_users = np.random.choice(train_users, sample_size, replace=False)
            print(f"📊 Sampling {sample_size} users from {len(train_users)} for Stage 2 training")
        else:
            sampled_users = train_users
            
        # Get features for sampled users
        sample_features = features_df[features_df['user_id'].isin(sampled_users)]
        sample_actuals = future_df[future_df['user_id'].isin(sampled_users)]
        
        # Generate meta-features (simplified approach)
        feature_cols = [col for col in sample_features.columns 
                       if col not in ['user_id', 'product_id']]
        X_sample = sample_features[feature_cols]
        
        # Get Stage 1 predictions
        stage1_probs = self.stage1_model.predict_proba(X_sample)[:, 1]
        sample_features['probability'] = stage1_probs
        
        # Create simple meta-features for Stage 2
        meta_features = []
        meta_labels = []
        
        thresholds = [0.1, 0.2, 0.3]
        
        for user_id in tqdm(sampled_users[:1000], desc="Generating meta-features"):  # Limit to 1000 users
            user_data = sample_features[sample_features['user_id'] == user_id]
            user_actuals = sample_actuals[sample_actuals['user_id'] == user_id]['product_id'].tolist()
            
            if user_data.empty:
                continue
                
            # Calculate meta-features for different thresholds
            meta_row = []
            f1_scores = []
            
            for threshold in thresholds:
                candidates = user_data[user_data['probability'] > threshold]['product_id'].tolist()
                
                if candidates:
                    meta_row.extend([
                        user_data[user_data['probability'] > threshold]['probability'].mean(),
                        user_data[user_data['probability'] > threshold]['probability'].max(),
                        len(candidates)
                    ])
                    
                    # Calculate F1 score
                    tp = len(set(candidates) & set(user_actuals))
                    precision = tp / len(candidates) if candidates else 0
                    recall = tp / len(user_actuals) if user_actuals else 0
                    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                    f1_scores.append(f1)
                else:
                    meta_row.extend([0, 0, 0])
                    f1_scores.append(0)
            
            if meta_row and f1_scores:
                meta_features.append(meta_row)
                meta_labels.append(np.argmax(f1_scores))
        
        if meta_features:
            X_meta = np.array(meta_features)
            y_meta = np.array(meta_labels)
            
            self.stage2_model.fit(X_meta, y_meta)
            print("✅ Stage 2 training complete")
        else:
            print("⚠️ Stage 2 training skipped - insufficient data")
        
        log_memory_usage("After Stage 2 training")
    
    def save_models(self, path="/app/models"):
        """Save both models"""
        print(f"💾 Saving models to {path}...")
        os.makedirs(path, exist_ok=True)
        
        joblib.dump(self.stage1_model, os.path.join(path, "stage1_lgbm.pkl"))
        joblib.dump(self.stage2_model, os.path.join(path, "stage2_gbc.pkl"))
        
        print("✅ Models saved successfully!")

# =====================================================================================
# MAIN TRAINING PIPELINE
# =====================================================================================

def main():
    """Optimized training pipeline with chunked processing"""
    print("🚀 OPTIMIZED ML Training Pipeline Starting...")
    log_memory_usage("Initial")
    
    # Auto-detect data paths
    data_path = "/app/training-data/"
    model_path = "/app/models/"
    
    print(f"📂 Loading data from: {data_path}")
    
    # Load data with memory optimization
    print("📥 Loading core datasets...")
    orders = pd.read_csv(os.path.join(data_path, "orders.csv"))
    orders = optimize_dataframe_memory(orders)
    
    order_products_prior = pd.read_csv(os.path.join(data_path, "order_products__prior.csv"))
    order_products_prior = optimize_dataframe_memory(order_products_prior)
    
    order_products_train = pd.read_csv(os.path.join(data_path, "order_products__train.csv"))
    order_products_train = optimize_dataframe_memory(order_products_train)
    
    log_memory_usage("After data loading")
    
    # Combine order products
    order_products_combined = pd.concat([order_products_prior, order_products_train], ignore_index=True)
    order_products_combined = optimize_dataframe_memory(order_products_combined)
    
    # Clean up individual datasets
    del order_products_prior, order_products_train
    gc.collect()
    
    log_memory_usage("After data preparation")
    
    # Define train/validation split
    train_users = orders[orders['eval_set'] == 'train']['user_id'].unique()
    print(f"👥 Training users: {len(train_users)}")
    
    # Initialize chunked feature engineer
    feature_engineer = ChunkedFeatureEngineer(chunk_size=1000)  # Smaller chunks for safety
    
    # Generate features using chunked processing
    features_df = feature_engineer.generate_all_features_chunked(orders, order_products_combined)
    
    log_memory_usage("After feature engineering")
    
    # Prepare training data
    print("📊 Preparing training datasets...")
    
    # Get ground truth
    future_df = order_products_train.merge(orders, on='order_id')[['user_id', 'product_id', 'order_id']]
    
    # Create training data for Stage 1
    train_features = features_df[features_df['user_id'].isin(train_users)]
    labels = future_df.merge(
        train_features[['user_id', 'product_id']], 
        on=['user_id', 'product_id'], 
        how='right'
    )
    labels['label'] = labels['order_id'].notna().astype(int)
    
    # Combine features with labels
    training_data = train_features.merge(
        labels[['user_id', 'product_id', 'label']], 
        on=['user_id', 'product_id']
    ).fillna(0)
    
    log_memory_usage("After training data preparation")
    
    # Split into train/validation
    split_point = int(0.8 * len(training_data))
    train_data = training_data[:split_point]
    val_data = training_data[split_point:]
    
    # Prepare features and labels
    feature_cols = [col for col in training_data.columns if col not in ['user_id', 'product_id', 'label']]
    
    X_train = train_data[feature_cols]
    y_train = train_data['label']
    X_val = val_data[feature_cols]
    y_val = val_data['label']
    
    log_memory_usage("Before model training")
    
    # Initialize and train model
    model = OptimizedStackedBasketModel()
    
    # Train Stage 1
    model.train_stage1(X_train, y_train, X_val, y_val)
    
    # Train Stage 2 with sampling
    model.train_stage2_with_sampling(features_df, future_df, train_users[:5000])  # Limit users for Stage 2
    
    # Save models
    model.save_models(model_path)
    
    log_memory_usage("Final")
    
    print("\n🎉🎉🎉 OPTIMIZED TRAINING COMPLETE! 🎉🎉🎉")
    print(f"✅ Models saved to {model_path}")
    print("✅ stage1_lgbm.pkl - LightGBM classifier")
    print("✅ stage2_gbc.pkl - Gradient boosting classifier")

if __name__ == "__main__":
    main()
