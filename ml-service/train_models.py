#!/usr/bin/env python3
"""
Simple Training Script to Create Working ML Models for User 347
Based on the quick_training.py script but simplified for immediate functionality
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.ensemble import GradientBoostingClassifier
import joblib
import os
import sys

print("🚀 Starting Simple ML Model Training...")

# ============================================================================
# 1. LOAD AND SAMPLE DATA (Memory Efficient)
# ============================================================================
print("📊 Loading and sampling data...")

# Load core datasets
try:
    orders = pd.read_csv('/app/training-data/orders.csv')
    order_products_prior = pd.read_csv('/app/training-data/order_products__prior.csv')
    order_products_train = pd.read_csv('/app/training-data/order_products__train.csv')
    products = pd.read_csv('/app/training-data/products.csv')
    print("✅ Data loaded successfully")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    sys.exit(1)

print(f"✅ Original data sizes:")
print(f"   Orders: {len(orders):,}")
print(f"   Prior products: {len(order_products_prior):,}")
print(f"   Train products: {len(order_products_train):,}")

# Sample a subset of users for memory efficiency (top 1000 most active users)
user_activity = orders.groupby('user_id')['order_number'].max().sort_values(ascending=False)
sample_users = user_activity.head(1000).index.tolist()

print(f"🎯 Training on {len(sample_users)} most active users for efficiency")

# Ensure user 347 is in the sample
if 347 not in sample_users:
    sample_users.append(347)
    print("✅ Added user 347 to training sample")

# Filter datasets to sample users
orders_sample = orders[orders['user_id'].isin(sample_users)]
prior_sample = order_products_prior.merge(orders_sample[['order_id']], on='order_id')
train_sample = order_products_train.merge(orders_sample[['order_id']], on='order_id')

print(f"✅ Sampled data sizes:")
print(f"   Orders: {len(orders_sample):,}")
print(f"   Prior products: {len(prior_sample):,}")
print(f"   Train products: {len(train_sample):,}")

# ============================================================================
# 2. FEATURE ENGINEERING (Simplified)
# ============================================================================
print("🔧 Generating features...")

# Combine prior and train
all_order_products = pd.concat([prior_sample, train_sample])

# User features
user_features = orders_sample.groupby('user_id').agg({
    'order_number': 'max',
    'days_since_prior_order': 'mean',
    'order_dow': lambda x: x.mode()[0] if len(x) > 0 else 0,
    'order_hour_of_day': lambda x: x.mode()[0] if len(x) > 0 else 0
}).round(2)

# Flatten column names
user_features.columns = ['user_total_orders', 'user_avg_days', 'user_fav_dow', 'user_fav_hour']
user_features = user_features.fillna(0)

# Product features
product_features = all_order_products.groupby('product_id').agg({
    'order_id': 'count',
    'reordered': 'mean'
}).round(3)
product_features.columns = ['product_orders', 'product_reorder_rate']
product_features = product_features.reset_index()  # Make product_id a column

# User-Product features
user_product_features = all_order_products.merge(orders_sample[['order_id', 'user_id', 'order_number']], on='order_id')
user_product_agg = user_product_features.groupby(['user_id', 'product_id']).agg({
    'order_id': 'count',
    'reordered': 'sum',
    'order_number': 'max'
}).round(2)
user_product_agg.columns = ['order_count', 'reorder_sum', 'up_last_order']

# Add "orders since last purchase"
user_product_agg = user_product_agg.merge(user_features[['user_total_orders']], on='user_id')
user_product_agg['up_orders_since_last'] = user_product_agg['user_total_orders'] - user_product_agg['up_last_order']

# Calculate reorder rate
user_product_agg['reorder_rate'] = user_product_agg['reorder_sum'] / user_product_agg['order_count']
user_product_agg = user_product_agg.fillna(0)

# Combine all features
features_df = user_product_agg.reset_index()  # This should have user_id and product_id as columns now
features_df = features_df.merge(user_features.drop(columns=['user_total_orders']), on='user_id', how='left')
features_df = features_df.merge(product_features, on='product_id', how='left')
features_df = features_df.fillna(0)

print(f"✅ Generated {len(features_df):,} feature rows for {features_df['user_id'].nunique()} users")

# ============================================================================
# 3. PREPARE TRAINING DATA (Compatible with SimpleStackedBasketModel)
# ============================================================================
print("📋 Preparing training labels...")

# Create ground truth from train set
ground_truth = train_sample.merge(orders_sample[['order_id', 'user_id']], on='order_id')[['user_id', 'product_id']]
ground_truth['will_reorder'] = 1

# Merge features with ground truth to create labels
training_data = features_df.merge(ground_truth, on=['user_id', 'product_id'], how='left')
training_data['will_reorder'] = training_data['will_reorder'].fillna(0).astype(int)

# Split users for train/validation
train_users = sample_users[:800]  # 80% for training
val_users = sample_users[800:]    # 20% for validation

train_data = training_data[training_data['user_id'].isin(train_users)]
val_data = training_data[training_data['user_id'].isin(val_users)]

# Use the exact 3 features that SimpleStackedBasketModel expects
feature_cols = ['order_count', 'reorder_sum', 'reorder_rate']

X_train = train_data[feature_cols].fillna(0)
y_train = train_data['will_reorder']
X_val = val_data[feature_cols].fillna(0)
y_val = val_data['will_reorder']

print(f"✅ Training set: {len(X_train):,} samples ({y_train.sum():,} positive)")
print(f"✅ Validation set: {len(X_val):,} samples ({y_val.sum():,} positive)")

# ============================================================================
# 4. TRAIN STAGE 1 MODEL (LightGBM)
# ============================================================================
print("🤖 Training Stage 1 Model (LightGBM)...")

stage1_model = lgb.LGBMClassifier(
    objective='binary',
    n_estimators=100,  # Reduced for speed
    learning_rate=0.1,
    num_leaves=32,
    random_state=42,
    verbosity=-1
)

stage1_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[lgb.early_stopping(20, verbose=False)]
)

print("✅ Stage 1 model trained successfully!")

# ============================================================================
# 5. PREPARE STAGE 2 DATA (Simple version)
# ============================================================================
print("🔄 Preparing Stage 2 training data...")

# Generate predictions for meta-features
train_probs = stage1_model.predict_proba(X_train)[:, 1]
train_data_with_probs = train_data.copy()
train_data_with_probs['probability'] = train_probs

# Define thresholds
thresholds = [0.2, 0.3, 0.4]

# Generate meta-features and find best baskets for each user (simplified)
meta_features_list = []
best_basket_list = []

for user_id in train_users[:50]:  # Sample smaller set for stage 2
    user_data = train_data_with_probs[train_data_with_probs['user_id'] == user_id]
    user_actual = user_data[user_data['will_reorder'] == 1]['product_id'].tolist()
    
    if len(user_actual) == 0:  # Skip users with no purchases
        continue
    
    baskets = []
    meta_features = []
    f1_scores = []
    
    for i, threshold in enumerate(thresholds):
        basket = user_data[user_data['probability'] > threshold]['product_id'].tolist()
        baskets.append(basket)
        
        # Calculate meta-features
        basket_probs = user_data[user_data['probability'] > threshold]['probability']
        if len(basket_probs) > 0:
            meta_features.extend([basket_probs.mean(), basket_probs.max(), basket_probs.min()])
        else:
            meta_features.extend([0, 0, 0])
        
        # Calculate F1 score
        if len(basket) > 0 and len(user_actual) > 0:
            tp = len(set(basket) & set(user_actual))
            precision = tp / len(basket) if len(basket) > 0 else 0
            recall = tp / len(user_actual) if len(user_actual) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            f1 = 0
        f1_scores.append(f1)
    
    # Find best basket
    best_basket_idx = np.argmax(f1_scores)
    
    meta_features_list.append(meta_features)
    best_basket_list.append(best_basket_idx)

# ============================================================================
# 6. TRAIN STAGE 2 MODEL (Gradient Boosting)
# ============================================================================
print("🎯 Training Stage 2 Model (Gradient Boosting)...")

if len(meta_features_list) > 0:
    X_meta = np.array(meta_features_list)
    y_meta = np.array(best_basket_list)
    
    stage2_model = GradientBoostingClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42
    )
    
    stage2_model.fit(X_meta, y_meta)
    print("✅ Stage 2 model trained successfully!")
else:
    print("⚠️ No valid meta-features generated, creating simple Stage 2 model...")
    # Create a simple classifier that just picks threshold 1 (middle)
    stage2_model = GradientBoostingClassifier(n_estimators=10, random_state=42)
    # Train on dummy data
    dummy_X = np.array([[0.5, 0.8, 0.3] * 3, [0.3, 0.6, 0.2] * 3])
    dummy_y = np.array([1, 0])
    stage2_model.fit(dummy_X, dummy_y)

# ============================================================================
# 7. SAVE MODELS
# ============================================================================
print("💾 Saving trained models...")

# Create models directory
os.makedirs('/app/models', exist_ok=True)

# Save models
joblib.dump(stage1_model, '/app/models/stage1_lgbm.pkl')
joblib.dump(stage2_model, '/app/models/stage2_gbc.pkl')

# Save feature columns for later use
feature_info = {
    'feature_columns': feature_cols,
    'thresholds': thresholds,
    'training_summary': {
        'users_trained': len(train_users),
        'samples_processed': len(X_train),
        'positive_samples': int(y_train.sum())
    }
}

import json
with open('/app/models/model_info.json', 'w') as f:
    json.dump(feature_info, f, indent=2)

print("✅ Models saved successfully!")
print("📂 Saved files:")
print("   - /app/models/stage1_lgbm.pkl")
print("   - /app/models/stage2_gbc.pkl") 
print("   - /app/models/model_info.json")

# ============================================================================
# 8. TEST MODELS
# ============================================================================
print("🧪 Testing model loading...")

try:
    # Test loading
    test_stage1 = joblib.load('/app/models/stage1_lgbm.pkl')
    test_stage2 = joblib.load('/app/models/stage2_gbc.pkl')
    
    # Test prediction on user 347 data
    user_347_data = features_df[features_df['user_id'] == 347]
    if not user_347_data.empty:
        X_347 = user_347_data[feature_cols].fillna(0)
        test_pred = test_stage1.predict_proba(X_347)
        print(f"✅ Model test successful! User 347 has {len(X_347)} products, sample predictions: {test_pred[:2, 1] if len(test_pred) > 0 else 'None'}")
    else:
        print("⚠️ User 347 not found in features")
    
except Exception as e:
    print(f"❌ Model test failed: {e}")

print("\n🎉 TRAINING COMPLETE! 🎉")
print("🔄 The ML service should now be able to load models and make predictions")
print("📊 You can now test predictions for user 347!")
