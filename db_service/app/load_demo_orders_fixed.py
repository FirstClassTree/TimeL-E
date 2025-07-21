#!/usr/bin/env python3
"""
Load Demo Orders Script - Fixed Version
Only loads orders for demo users that exist in the database
"""

import os
import csv
import traceback
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.orders import Order, OrderItem

CSV_DIR = "/app/csv_data"
DEMO_USERS = [347, 688, 82420, 43682, 39993]

def load_demo_orders():
    db: Session = SessionLocal()
    
    print("🛒 Loading demo orders from CSV...")
    
    # Check if demo users have orders
    demo_user_orders = db.query(Order).filter(Order.user_id.in_(DEMO_USERS)).count()
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
        
        # Load orders first - ONLY for demo users
        orders_loaded = 0
        batch_size = 50
        batch_orders = []
        
        print("📋 Loading orders...")
        with open(orders_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    user_id = int(row['user_id'])
                    
                    # ONLY load orders for demo users
                    if user_id not in DEMO_USERS:
                        continue
                        
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
                        user_id=user_id,
                        eval_set=row['eval_set'],
                        order_number=int(row['order_number']),
                        order_dow=int(row['order_dow']),
                        order_hour_of_day=int(row['order_hour_of_day']),
                        days_since_prior_order=days_since_prior,
                        total_items=0  # Will be calculated from items
                    )
                    
                    batch_orders.append(order)
                    orders_loaded += 1
                    
                    print(f"   ✅ Order {row['order_id']} for user {row['user_id']}")
                    
                    # Commit in smaller batches for demo users
                    if len(batch_orders) >= batch_size:
                        db.add_all(batch_orders)
                        db.commit()  # Commit each batch immediately
                        print(f"   💾 Committed batch of {len(batch_orders)} orders")
                        batch_orders = []
                        
                except Exception as row_error:
                    print(f"   ❌ Error processing order {row.get('order_id', 'unknown')}: {row_error}")
                    continue
            
            # Commit remaining orders
            if batch_orders:
                db.add_all(batch_orders)
                db.commit()
                print(f"   💾 Committed final batch of {len(batch_orders)} orders")
        
        print(f"✅ Loaded {orders_loaded} orders")
        
        # Get demo order IDs that were successfully loaded
        demo_order_ids = set()
        for order in db.query(Order).filter(Order.user_id.in_(DEMO_USERS)).all():
            demo_order_ids.add(order.order_id)
        
        print(f"Found {len(demo_order_ids)} demo orders to load items for")
        
        # Load order items for demo orders only
        items_loaded = 0
        batch_items = []
        
        print("📦 Loading order items...")
        with open(order_items_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    order_id = int(row['order_id'])
                    if order_id not in demo_order_ids:
                        continue
                        
                    # Check if item already exists
                    existing = db.query(OrderItem).filter(
                        OrderItem.order_id == order_id,
                        OrderItem.product_id == int(row['product_id'])
                    ).first()
                    if existing:
                        continue
                    
                    # Get quantity if available, default to 1
                    quantity = 1
                    if 'quantity' in row and row['quantity']:
                        quantity = int(row['quantity'])
                    
                    item = OrderItem(
                        order_id=order_id,
                        product_id=int(row['product_id']),
                        add_to_cart_order=int(row['add_to_cart_order']),
                        reordered=int(row['reordered']),
                        quantity=quantity
                    )
                    
                    batch_items.append(item)
                    items_loaded += 1
                    
                    if items_loaded <= 10:
                        print(f"   ✅ Item {row['product_id']} in order {row['order_id']}")
                    
                    # Commit in smaller batches
                    if len(batch_items) >= batch_size:
                        db.add_all(batch_items)
                        db.commit()
                        print(f"   💾 Committed batch of {len(batch_items)} items")
                        batch_items = []
                        
                except Exception as row_error:
                    print(f"   ❌ Error processing item: {row_error}")
                    continue
            
            # Commit remaining items
            if batch_items:
                db.add_all(batch_items)
                db.commit()
                print(f"   💾 Committed final batch of {len(batch_items)} items")
        
        print(f"✅ Loaded {items_loaded} order items")
        
        # Update total_items count for orders
        print("🔢 Updating order total_items counts...")
        orders_to_update = db.query(Order).filter(Order.user_id.in_(DEMO_USERS), Order.total_items == 0).all()
        for order in orders_to_update:
            item_count = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).count()
            order.total_items = item_count
        
        print("💾 Final commit...")
        db.commit()
        print("✅ Demo orders successfully loaded!")
        
        # Verification
        final_orders = db.query(Order).filter(Order.user_id.in_(DEMO_USERS)).count()
        final_items = db.query(OrderItem).join(Order).filter(Order.user_id.in_(DEMO_USERS)).count()
        
        print(f"📊 Final counts:")
        print(f"   Demo orders: {final_orders}")
        print(f"   Demo items: {final_items}")
        
        # Show sample demo user orders
        print("🔍 Demo user orders:")
        for user_id in DEMO_USERS:
            user_orders = db.query(Order).filter(Order.user_id == user_id).count()
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
