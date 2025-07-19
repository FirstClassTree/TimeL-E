#!/usr/bin/env python3
"""
Load demo users and their orders into the database
"""
import os
import csv

from .database import SessionLocal
from .models.users import User
from .models.orders import Order, OrderItem

def load_demo_users():
    """Load ALL demo users from CSV and their prior orders"""
    db = SessionLocal()
    
    try:
        print("Loading ALL users from users_demo.csv...")
        
        # Load users from CSV
        users_loaded = 0
        with open('/app/csv_data/users_demo.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_id = int(row['user_id'])
                # Check if user already exists
                existing_user = db.query(User).filter(User.user_id == user_id).first()
                if not existing_user:
                    user = User(
                        user_id=user_id,
                        name=row['name'],
                        hashed_password=row['hashed_password'],
                        email_address=row['email_address'],
                        phone_number=row['phone_number'],
                        street_address=row['street_address'],
                        city=row['city'],
                        postal_code=row['postal_code'],
                        country=row['country']
                    )
                    db.add(user)
                    users_loaded += 1
                    if users_loaded <= 10:  # Show first 10 for confirmation
                        print(f"Added user {user_id}: {row['name']}")
        
        # Load their orders (only "prior" eval_set to avoid train/test contamination)
        orders_loaded = 0
        with open('/app/csv_data/orders_demo.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_id = int(row['user_id'])
                # Check if user exists in our loaded users and load prior orders
                user_exists = db.query(User).filter(User.user_id == user_id).first()
                if user_exists and row['eval_set'] == 'prior':
                    # Check if order already exists
                    order_id = int(row['order_id'])
                    existing_order = db.query(Order).filter(Order.order_id == order_id).first()
                    if not existing_order:
                        order = Order(
                            order_id=order_id,
                            user_id=user_id,
                            order_number=int(row['order_number']),
                            order_dow=int(row['order_dow']),
                            order_hour_of_day=int(row['order_hour_of_day']),
                            days_since_prior_order=float(row['days_since_prior_order']) if row['days_since_prior_order'] else None
                        )
                        db.add(order)
                        orders_loaded += 1
        
        # Load order items
        order_items_loaded = 0
        with open('/app/csv_data/order_items_demo.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = int(row['order_id'])
                # Check if this order belongs to our demo users
                order = db.query(Order).filter(Order.order_id == order_id).first()
                if order:
                    # Check if order item already exists
                    existing_item = db.query(OrderItem).filter(
                        OrderItem.order_id == order_id,
                        OrderItem.product_id == int(row['product_id'])
                    ).first()
                    if not existing_item:
                        order_item = OrderItem(
                            order_id=order_id,
                            product_id=int(row['product_id']),
                            add_to_cart_order=int(row['add_to_cart_order']),
                            reordered=bool(int(row['reordered']))
                        )
                        db.add(order_item)
                        order_items_loaded += 1
        
        db.commit()
        print(f"✅ Successfully loaded:")
        print(f"   {users_loaded} users")
        print(f"   {orders_loaded} orders")
        print(f"   {order_items_loaded} order items")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading demo data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_demo_users()
