#!/usr/bin/env python3
"""
Load Demo Orders Script
Loads orders_demo.csv and order_items_demo.csv into the database
"""

import os
import csv
import traceback
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.orders import Order, OrderItem

CSV_DIR = "/app/csv_data"

def load_demo_orders():
    db: Session = SessionLocal()
    
    print("🛒 Loading demo orders from CSV...")
    
    # Check if orders already exist
    orders_exist = db.query(Order).first() is not None
    if orders_exist:
        print("Orders already exist in database.")
        existing_count = db.query(Order).count()
        print(f"Current order count: {existing_count}")
        
        # Check if demo users have orders
        demo_user_orders = db.query(Order).filter(Order.user_id.in_([347, 688, 82420, 43682, 39993])).count()
        print(f"Demo users orders count: {demo_user_orders}")
        
        if demo_user_orders > 0:
            print("Demo users already have orders. Skipping load.")
            db.close()
            return
    
    try:
        orders_file = os.path.join(CSV_DIR, "orders_demo.csv")
        order_items_file = os.path.join(CSV_DIR, "order_items_demo.csv")
        
        print(f"📋 Orders file: {orders_file}")
        print(f"📦 Order items file: {order_items_file}")
        
        if not os.path.exists(orders_file):
            print(f"❌ Orders file not found: {orders_file}")
            return
            
        if not os.path.exists(order_items_file):
            print(f"❌ Order items file not found: {order_items_file}")
            return
        
        # Load orders first
        orders_loaded = 0
        batch_size = 100
        batch_orders = []
        
        print("📋 Loading orders...")
        with open(orders_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print(f"Orders CSV columns: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Check if order already exists
                    existing = db.query(Order).filter(Order.order_id == int(row['order_id'])).first()
                    if existing:
                        continue
                    
                    # Parse days_since_prior_order
                    days_since_prior = None
                    if row['days_since_prior_order'] and row['days_since_prior_order'].strip():
                        try:
                            days_since_prior = float(row['days_since_prior_order'])
                        except ValueError:
                            days_since_prior = None
                    
                    order = Order(
                        order_id=int(row['order_id']),
                        user_id=int(row['user_id']),
                        eval_set=row['eval_set'],
                        order_number=int(row['order_number']),
                        order_dow=int(row['order_dow']),
                        order_hour_of_day=int(row['order_hour_of_day']),
                        days_since_prior_order=days_since_prior,
                        total_items=0  # Will be calculated from items
                    )
                    
                    batch_orders.append(order)
                    orders_loaded += 1
                    
                    if orders_loaded <= 5:
                        print(f"   ✅ Row {row_num}: Order {row['order_id']} for user {row['user_id']}")
                    
                    # Commit in batches
                    if len(batch_orders) >= batch_size:
                        db.add_all(batch_orders)
                        db.flush()
                        print(f"   💾 Committed batch of {len(batch_orders)} orders")
                        batch_orders = []
                        
                except Exception as row_error:
                    print(f"   ❌ Row {row_num}: Error processing order {row.get('order_id', 'unknown')}: {row_error}")
            
            # Commit remaining orders
            if batch_orders:
                db.add_all(batch_orders)
                db.flush()
                print(f"   💾 Committed final batch of {len(batch_orders)} orders")
        
        print(f"✅ Loaded {orders_loaded} orders")
        
        # Load order items
        items_loaded = 0
        batch_items = []
        
        print("📦 Loading order items...")
        with open(order_items_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print(f"Order items CSV columns: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Check if item already exists
                    existing = db.query(OrderItem).filter(
                        OrderItem.order_id == int(row['order_id']),
                        OrderItem.product_id == int(row['product_id'])
                    ).first()
                    if existing:
                        continue
                    
                    # Get quantity if available, default to 1
                    quantity = 1
                    if 'quantity' in row and row['quantity']:
                        quantity = int(row['quantity'])
                    
                    item = OrderItem(
                        order_id=int(row['order_id']),
                        product_id=int(row['product_id']),
                        add_to_cart_order=int(row['add_to_cart_order']),
                        reordered=int(row['reordered']),
                        quantity=quantity
                    )
                    
                    batch_items.append(item)
                    items_loaded += 1
                    
                    if items_loaded <= 5:
                        print(f"   ✅ Row {row_num}: Item {row['product_id']} in order {row['order_id']}")
                    
                    # Commit in batches
                    if len(batch_items) >= batch_size:
                        db.add_all(batch_items)
                        db.flush()
                        print(f"   💾 Committed batch of {len(batch_items)} items")
                        batch_items = []
                        
                except Exception as row_error:
                    print(f"   ❌ Row {row_num}: Error processing item: {row_error}")
            
            # Commit remaining items
            if batch_items:
                db.add_all(batch_items)
                db.flush()
                print(f"   💾 Committed final batch of {len(batch_items)} items")
        
        print(f"✅ Loaded {items_loaded} order items")
        
        # Update total_items count for orders
        print("🔢 Updating order total_items counts...")
        orders_to_update = db.query(Order).filter(Order.total_items == 0).all()
        for order in orders_to_update:
            item_count = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).count()
            order.total_items = item_count
        
        print("💾 Committing all changes...")
        db.commit()
        print("✅ Demo orders successfully loaded!")
        
        # Verification
        final_orders = db.query(Order).count()
        final_items = db.query(OrderItem).count()
        demo_orders = db.query(Order).filter(Order.user_id.in_([347, 688, 82420, 43682, 39993])).count()
        
        print(f"📊 Final counts:")
        print(f"   Total orders: {final_orders}")
        print(f"   Total items: {final_items}")
        print(f"   Demo user orders: {demo_orders}")
        
        # Show sample demo user orders
        print("🔍 Sample demo user orders:")
        for user_id in [347, 688, 82420, 43682, 39993]:
            user_orders = db.query(Order).filter(Order.user_id == user_id).count()
            if user_orders > 0:
                print(f"   User {user_id}: {user_orders} orders")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during orders loading: {e}")
        print("Full error details:")
        traceback.print_exc()
        try:
            db.rollback()
            print("🔄 Database rolled back successfully")
        except Exception as rollback_error:
            print(f"❌ Error during rollback: {rollback_error}")
    finally:
        db.close()

if __name__ == "__main__":
    load_demo_orders()
