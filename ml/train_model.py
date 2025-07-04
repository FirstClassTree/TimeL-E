# ml/train_model.py

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

DATA_PATH = "data/shopping_carts.csv"
MODEL_PATH = "ml/model.pkl"

def load_data(path=DATA_PATH):
    """Load and return the raw dataset."""
    return pd.read_csv(path)

def preprocess(df):
    """
    Transform raw cart data into a user-item matrix suitable for training.
    For demo purposes: predicting likelihood of purchasing a specific item.
    """
    user_item = df.pivot_table(
        index='user_id', columns='item_id', values='quantity', fill_value=0
    )

    target_item = user_item.columns[0]  # Pick one item to predict
    X = user_item.drop(columns=[target_item])
    y = (user_item[target_item] > 0).astype(int)

    return train_test_split(X, y, test_size=0.2, random_state=42)

def train_model(X_train, y_train):
    """Train and return a model."""
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    """Print evaluation metrics."""
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

def save_model(model, path=MODEL_PATH):
    """Save model to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"✅ Model saved to {path}")

def main():
    df = load_data()
    X_train, X_test, y_train, y_test = preprocess(df)
    model = train_model(X_train, y_train)
    evaluate_model(model, X_test, y_test)
    save_model(model)

if __name__ == "__main__":
    main()
