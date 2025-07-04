# backend/ml_predictor.py

model = None

def load_model():
    global model
    # Replace with actual loading logic
    model = "dummy-model"

def predict_next_cart(user_id):
    # Replace with actual prediction logic using `model`
    # For now, return a mock list of items
    return [
        {"item_id": "item101", "quantity": 2},
        {"item_id": "item204", "quantity": 1}
    ]
