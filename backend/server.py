# backend/server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import initialize_db, insert_cart_item, get_all_cart_data
from ml_predictor import load_model, predict_next_cart  # <- Import ML model utils

app = FastAPI()

class CartItem(BaseModel):

    # Needs to add more as neccarry
    user_id: str
    item_id: str
    quantity: int

class PredictRequest(BaseModel):
    user_id: str

@app.on_event("startup")
def startup_event():
    initialize_db()
    load_model()  # <- Load ML model on startup

@app.post("/cart/")
def add_cart_item(item: CartItem):
    try:
        insert_cart_item(item.user_id, item.item_id, item.quantity)
        return {"message": "Item added to cart"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cart/")
def fetch_cart_data():
    try:
        data = get_all_cart_data()
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/")
def predict_cart(request: PredictRequest):
    try:
        prediction = predict_next_cart(request.user_id)
        return {"predicted_cart": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
