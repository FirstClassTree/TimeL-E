#!/usr/bin/env python3
"""
Populate order.created_at and order_status_history, order.status, order.updated_at from generated CSVs.
"""


import traceback
import os
from datetime import datetime, UTC
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.db_core.database import SessionLocal
from app.db_core.models import Order, OrderStatusHistory, OrderStatus
import csv
from collections import defaultdict
import pandas as pd

CSV_DIR = "/data"

def parse_dt(dt_str):
    if not dt_str or pd.isna(dt_str):
        return None
    # Always use explicit format matching CSV export
    try:
        # Try ISO first (with timezone)
        return datetime.fromisoformat(dt_str)
    except Exception:
        # Fallback: try common CSV datetime
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S%z")
        except Exception:
            # Try without timezone (as a last resort)
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

def is_today(dt):
    if not dt:
        return False
    now = datetime.now(UTC)
    return dt.date() == now.date()

def populate_orders_created_at():
    """
    Update the created_at field of orders from orders_demo_enriched.csv
    This will be skipped if orders were loaded when created_at timestamps existed.
    """
    try:
        # Create database session
        db = SessionLocal()

        filename = os.path.join(CSV_DIR, "orders_demo_enriched.csv")
        if not os.path.exists(filename):
            print(f"[orders_demo_enriched.csv] not found, skipping created_at update.")
            return

        with open(filename, newline='') as f:
            reader = csv.DictReader(f)
            first_row = next(reader, None)
            if not first_row:
                print("orders_demo_enriched.csv is empty, skipping created_at update.")
                db.close()
                return
            first_order_id = int(first_row['order_id'])
            order = db.query(Order).filter(Order.id == first_order_id).first()
            if order and order.created_at is not None and not is_today(order.created_at):
                print(f"Order.created_at already set for order_id {first_order_id} ({order.created_at}); skipping all created_at loading.")
                db.close()
                return

        print(f"Updating orders.created_at from: {filename}")
        batch_size = 50  # Reduced for memory stability
        batch_orders = []
        updated, missing, errors = 0, 0, 0

        with open(filename, newline='') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    order_id = int(row['order_id'])
                    created_at = parse_dt(row['created_at'])
                    order = db.query(Order).filter(Order.id == order_id).first()
                    if order:
                        order.created_at = created_at
                        batch_orders.append(order)
                        updated += 1
                    else:
                        missing += 1

                    if len(batch_orders) >= batch_size:
                        try:
                            db.flush()
                            batch_orders = []
                        except (IntegrityError, SQLAlchemyError) as batch_err:
                            db.rollback()
                            print(f"   ERROR: Batch update failed at row {row_num} (will try individually): {batch_err}")
                            for single_order in batch_orders:
                                try:
                                    db.flush()
                                except (IntegrityError, SQLAlchemyError) as row_err:
                                    errors += 1
                                    db.rollback()
                                    print(f"      -> Skipping bad order update (order_id {single_order.order_id}): {row_err}")
                            batch_orders = []
                except Exception as e:
                    errors += 1
                    print(f"   Row {row_num}: Error updating created_at for order_id {row.get('order_id','?')}: {e}")

        if batch_orders:
            try:
                db.flush()
            except (IntegrityError, SQLAlchemyError) as batch_err:
                db.rollback()
                print(f"   ERROR: Final batch update failed (will try individually): {batch_err}")
                for single_order in batch_orders:
                    try:
                        db.flush()
                    except (IntegrityError, SQLAlchemyError) as row_err:
                        errors += 1
                        db.rollback()
                        print(f"      -> Skipping bad order update (order_id {single_order.order_id}): {row_err}")

        db.commit()
        print(f"orders.created_at updated for {updated} orders (missing: {missing}, errors: {errors})")
    except Exception as e:
        print(f"CRITICAL ERROR during CSV loading: {e}")
        print("Full error details:")
        traceback.print_exc()
        try:
            db.rollback()
            print("Database rolled back successfully")
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
    finally:
        db.close()

def normalize_status(status):
    if status is None:
        return None
    s = status.strip().lower()
    allowed = {e.value for e in OrderStatus}
    if s in allowed:
        return s
    print(f"WARNING: '{status}' is not a valid OrderStatus value! Skipping this record.")
    return None

def populate_order_status_history():
    """
    Load historical status rows from orders_demo_status_history.csv
    Populate old_status/new_status for each order in chronological order.
    Update Order.status and Order.updated_at to last status/date from CSV.
    """

    db = None
    try:
        db = SessionLocal()
        
        # Disable trigger to prevent automatic status history creation
        db.execute(text("ALTER TABLE orders.orders DISABLE TRIGGER trg_order_status_change"))
        db.commit()

        data_exists = db.query(OrderStatusHistory).first() is not None

        if data_exists:
            print("Order status history data already exists. Skipping population.")
            return True

        filename = os.path.join(CSV_DIR, "orders_demo_status_history.csv")
        if not os.path.exists(filename):
            print(f"[orders_demo_status_history.csv] not found, skipping status history import.")
            return

        print(f"Loading order status history from: {filename}")

        # Step 1: Group status rows in-memory per order
        order_histories = defaultdict(list)
        last_status_per_order = {}  # {order_id: (new_status, changed_at)}
        with open(filename, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = int(row['order_id'])
                status = row['status']
                changed_at = parse_dt(row['changed_at'])
                order_histories[order_id].append((changed_at, status))
                # Track the latest status and timestamp
                if (order_id not in last_status_per_order or
                        changed_at > last_status_per_order[order_id][1]):
                    last_status_per_order[order_id] = (status, changed_at)

        # Step 2: Batch-insert by order, keeping correct old/new status per order
        batch_size = 200
        batch = []
        count, errors = 0, 0

        for order_id, events in order_histories.items():
            # Sort events chronologically
            events.sort()
            prev_status = None
            for event_num, (changed_at, new_status) in enumerate(events, 1):
                try:
                    history = OrderStatusHistory(
                        order_id=order_id,
                        old_status=prev_status,
                        new_status=new_status,
                        changed_at=changed_at,
                        changed_by=None,
                        note=None
                    )
                    batch.append(history)
                    count += 1
                    prev_status = new_status

                    if len(batch) >= batch_size:
                        try:
                            db.add_all(batch)
                            db.flush()
                            batch = []
                        except (IntegrityError, SQLAlchemyError) as batch_err:
                            db.rollback()
                            print(f"   ERROR: Batch insert failed at order {order_id} (will try individually): {batch_err}")
                            for single_history in batch:
                                try:
                                    db.add(single_history)
                                    db.flush()
                                except (IntegrityError, SQLAlchemyError) as row_err:
                                    errors += 1
                                    db.rollback()
                                    if errors < 10:
                                        print(f"      -> Skipping bad status history (order_id {single_history.order_id}): {row_err}")
                            batch = []
                except Exception as e:
                    errors += 1
                    print(f"   Order {order_id}, event {event_num}: Error creating status history: {e}")

        if batch:
            try:
                db.add_all(batch)
                db.flush()
            except (IntegrityError, SQLAlchemyError) as batch_err:
                db.rollback()
                print(f"   ERROR: Final batch insert failed (will try individually): {batch_err}")
                for single_history in batch:
                    try:
                        db.add(single_history)
                        db.flush()
                    except (IntegrityError, SQLAlchemyError) as row_err:
                        errors += 1
                        db.rollback()
                        if errors < 10:
                            print(f"      -> Skipping bad status history (order_id {single_history.order_id}): {row_err}")

        db.commit()
        updated_orders, missing_orders, errors = 0, 0, 0
        batch_orders = []
        batch_size = 200

        for idx, (order_id, (last_status, last_changed_at)) in enumerate(last_status_per_order.items(), 1):
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = last_status
                order.updated_at = last_changed_at
                batch_orders.append(order)
                updated_orders += 1
            else:
                missing_orders += 1

            if len(batch_orders) >= batch_size:
                try:
                    db.flush()
                    batch_orders = []
                except (IntegrityError, SQLAlchemyError) as batch_err:
                    db.rollback()
                    print(f"   ERROR: Batch order update failed at idx {idx} (will try individually): {batch_err}")
                    for single_order in batch_orders:
                        try:
                            db.flush()
                        except (IntegrityError, SQLAlchemyError) as row_err:
                            errors += 1
                            db.rollback()
                            print(f"      -> Skipping bad order update (order_id {single_order.order_id}): {row_err}")
                    batch_orders = []

        if batch_orders:
            try:
                db.flush()
            except (IntegrityError, SQLAlchemyError) as batch_err:
                db.rollback()
                print(f"   ERROR: Final batch order update failed (will try individually): {batch_err}")
                for single_order in batch_orders:
                    try:
                        db.flush()
                    except (IntegrityError, SQLAlchemyError) as row_err:
                        errors += 1
                        db.rollback()
                        print(f"      -> Skipping bad order update (order_id {single_order.order_id}): {row_err}")

        db.commit()
        print(f"Orders updated from CSV: {updated_orders} (missing: {missing_orders})")
        
        # Re-enable trigger after updates
        db.execute(text("ALTER TABLE orders.orders ENABLE TRIGGER trg_order_status_change"))
        db.commit()

    except Exception as e:
        print(f"CRITICAL ERROR during CSV loading: {e}")
        print("Full error details:")
        traceback.print_exc()
        try:
            if db:  # Check if db is defined
                # Attempt to re-enable trigger even in case of error
                db.execute(text("ALTER TABLE orders.orders ENABLE TRIGGER trg_order_status_change"))
                db.commit()
        except:
            pass
        try:
            if db:  # Check if db is defined
                db.rollback()
                print("Database rolled back successfully")
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
    finally:
        if db:  # Check if db is defined before closing
            db.close()


def main():
    populate_orders_created_at()
    populate_order_status_history()

if __name__ == "__main__":
    main()
