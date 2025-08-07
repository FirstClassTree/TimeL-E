#!/usr/bin/env python3
"""
Populate enriched product data from CSV file.

Use --force-reset to delete all old data before populating.
Otherwise, populates only if table is empty.
"""

import pandas as pd
import sys
import argparse
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session
from .db_core.config import settings
from .db_core.database import SessionLocal
from .db_core.models import Department, Order, OrderItem, ProductEnriched


def populate_enriched_departments(session: Session):
    """Enrich Departments Table from departments_enriched.csv"""

    try:
        departments_csv_path = Path("/data/departments_enriched.csv")
        if departments_csv_path.exists():
            dept_df = pd.read_csv(departments_csv_path)
            # Normalize column names
            dept_df.columns = [c.strip().lower() for c in dept_df.columns]
            required_dept_cols = {"department_id", "description", "image_url"}
            if not required_dept_cols.issubset(dept_df.columns):
                print(f"Warning: departments_enriched.csv missing required columns. Found: {list(dept_df.columns)}")
            else:
                updated_count = 0
                for _, row in dept_df.iterrows():
                    dept_id = int(row['department_id'])
                    # Fetch department by department_id
                    dept = session.query(Department).filter_by(department_id=dept_id).first()
                    if dept:
                        dept.description = row['description'] if pd.notna(row['description']) else None
                        dept.image_url = row['image_url'] if pd.notna(row['image_url']) else None
                        updated_count += 1
                    else:
                        print(f"   Warning: No Department found with department_id {dept_id}. Skipping.")
                session.commit()
                print(f"Updated {updated_count} departments from departments_enriched.csv.")
        else:
            print(f"departments_enriched.csv not found at {departments_csv_path}, skipping department enrichment.")
    except Exception as dept_err:
        session.rollback()
        print(f"Error updating departments from enriched CSV: {dept_err}")


def populate_enriched_data(force_reset=False):
    """Populate the product_enriched table from CSV"""

    # Use /data/products_enriched/ (/data is a mounted volume)
    enriched_dir = Path("/data/products_enriched")
    csv_files = sorted(enriched_dir.glob("enriched_products_dept*.csv"))

    if not csv_files:
        print(f"Error: No enriched product CSV files found in {enriched_dir}")
        print("Make sure enriched data was generated using the product_enricher.py script and that /data is mounted correctly")
        return False
    else:
        print(f"Found enriched product CSV files: {[str(f) for f in csv_files]}")


    # Create database session
    session = SessionLocal()

    try:
        data_exists = session.query(ProductEnriched).first() is not None

        if not force_reset and data_exists:
            print("Enriched product data already exists. Skipping population.")
            return True

        if force_reset and data_exists:
            print("Force reset: clearing existing enriched data...")
            session.execute(text("DELETE FROM products.product_enriched"))
            session.commit()

        try:
            # Combine all department CSVs
            dfs = []
            for csv_file in csv_files:
                print(f"Reading enriched data from {csv_file}")
                df = pd.read_csv(csv_file)
                dfs.append(df)
            combined_df = pd.concat(dfs, ignore_index=True)
            print(f"Found {len(combined_df)} enriched products (all departments)")

            # Validate CSV structure
            required_columns = ['product_id', 'product_name', 'description', 'price', 'image_url']
            if not all(col in combined_df.columns for col in required_columns):
                print(f"Error: CSV missing required columns. Found: {list(combined_df.columns)}")
                return False

        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return False

        print("Inserting enriched product data...")

        success_count = 0
        error_count = 0

        BATCH_SIZE = 50  # Reduced for memory stability

        for batch_start in range(0, len(combined_df), BATCH_SIZE):
            batch_end = batch_start + BATCH_SIZE
            batch = combined_df.iloc[batch_start:batch_end]
            objects = []
            for _, row in batch.iterrows():
                try:
                    enriched = ProductEnriched(
                        product_id=int(row['product_id']),
                        description=row['description'] if pd.notna(row['description']) else None,
                        price=float(row['price']) if pd.notna(row['price']) else None,
                        image_url=row['image_url'] if pd.notna(row['image_url']) else None
                    )
                    objects.append(enriched)
                except Exception as e:
                    error_count += 1
                    print(f"   Warning: Failed to build product {row.get('product_id', 'unknown')}: {e}")
                    continue

            try:
                session.add_all(objects)
                session.flush()  # Use commit if need to persist each batch immediately
                success_count += len(objects)
                if success_count % 10000 == 0:
                    print(f"   Processed {success_count} products...")
            except Exception as batch_err:
                session.rollback()
                print(f"   ERROR: Batch insert failed: {batch_err} (will try individual rows)")
                # Fallback: try each row individually
                for obj in objects:
                    try:
                        new_obj = ProductEnriched(
                            product_id=obj.product_id,
                            description=obj.description,
                            price=obj.price,
                            image_url=obj.image_url
                        )
                        session.add(new_obj)
                        session.flush()
                        success_count += 1
                    except Exception as row_err:
                        error_count += 1
                        session.rollback()
                        print(f"      -> Skipping product {getattr(obj, 'product_id', '?')}: {row_err}")

        session.commit()

        print(f"\nSuccessfully populated enriched data!")
        print(f"   Inserted: {success_count} products")
        if error_count > 0:
            print(f"   Errors: {error_count} products")

        # Verify data
        result = session.execute(text("SELECT COUNT(*) FROM products.product_enriched")).scalar()
        print(f"Total enriched products in database: {result}")

        # After loading enriched products, update existing order item prices and order totals
        print("\nUpdating existing order item prices and order totals...")
        update_order_prices_from_enriched_data(session)

        populate_enriched_departments(session)

        return True

    except Exception as e:
        session.rollback()
        print(f"Error during database operations: {e}")
        # traceback.print_exc()
        return False

    finally:
        session.close()


def update_order_prices_from_enriched_data(session):
    """
    Update existing order item prices based on enriched product prices,
    then recalculate order total prices as sum of item prices.
    """
    try:
        print("   Updating order item prices from enriched product data...")
        
        # Get product_id and price mappings from enriched data
        enriched_prices = session.query(
            ProductEnriched.product_id, 
            ProductEnriched.price
        ).filter(
            ProductEnriched.price.isnot(None),
            ProductEnriched.price > 0
        ).all()
        
        # Create a dictionary for fast lookup
        price_lookup = {product_id: price for product_id, price in enriched_prices}
        print(f"   Found {len(price_lookup)} products with enriched prices")
        
        # Process order items in batches
        BATCH_SIZE = 1000
        updated_items = 0
        failed_batches = 0
        
        # Get total count for progress tracking
        total_items = session.query(OrderItem).count()
        print(f"   Processing {total_items} order items in batches of {BATCH_SIZE}")
        
        offset = 0
        while True:
            # Get batch of order items
            batch_items = session.query(OrderItem).offset(offset).limit(BATCH_SIZE).all()
            
            if not batch_items:
                break
            
            try:
                batch_updated = 0
                for item in batch_items:
                    if item.product_id in price_lookup:
                        item.price = price_lookup[item.product_id]
                        batch_updated += 1

                # Commit this batch
                session.commit()
                updated_items += batch_updated
                
                # Show progress every 10k items
                if offset % 10000 == 0 or offset + BATCH_SIZE >= total_items:
                    print(f"   Processed {min(offset + BATCH_SIZE, total_items)}/{total_items} items, updated {batch_updated} in this batch")
                    
            except Exception as batch_err:
                session.rollback()
                failed_batches += 1
                print(f"   ERROR: Failed to update batch at offset {offset}: {batch_err}")
                # Continue with next batch
            
            offset += BATCH_SIZE
        
        print(f"   Total updated: {updated_items} order items with enriched prices")
        if failed_batches > 0:
            print(f"   Failed batches: {failed_batches}")
        
        # Update order total prices in batches
        print("   Recalculating order total prices...")
        
        total_orders = session.query(Order).count()
        print(f"   Processing {total_orders} orders in batches of {BATCH_SIZE}")
        
        updated_orders = 0
        failed_order_batches = 0
        offset = 0
        
        while True:
            # Get batch of orders
            batch_orders = session.query(Order).offset(offset).limit(BATCH_SIZE).all()
            
            if not batch_orders:
                break
            
            try:
                batch_updated = 0
                for order in batch_orders:
                    # Calculate total price from order items
                    total_price = sum(item.price * item.quantity for item in order.order_items if item.price)
                    order.total_price = total_price
                    batch_updated += 1
                
                # Commit this batch
                session.commit()
                updated_orders += batch_updated
                
                # Show progress every 10k orders
                if offset % 10000 == 0 or offset + BATCH_SIZE >= total_orders:
                    print(f"   Processed {min(offset + BATCH_SIZE, total_orders)}/{total_orders} orders")
                    
            except Exception as batch_err:
                session.rollback()
                failed_order_batches += 1
                print(f"   ERROR: Failed to update order batch at offset {offset}: {batch_err}")
                # Continue with next batch
            
            offset += BATCH_SIZE
        
        print(f"   Updated {updated_orders} orders with recalculated total prices")
        if failed_order_batches > 0:
            print(f"   Failed order batches: {failed_order_batches}")
        
        # Verify the updates
        orders_with_price = session.query(Order).filter(Order.total_price > 0).count()
        avg_price_result = session.query(Order.total_price).filter(Order.total_price > 0).all()
        avg_total_price = sum(price[0] for price in avg_price_result) / len(avg_price_result) if avg_price_result else 0
        
        print(f"   Verification: {orders_with_price}/{total_orders} orders have prices > 0")
        print(f"   Average order total: ${avg_total_price:.2f}" if avg_total_price else "   Average order total: $0.00")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   Error updating order prices: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Populate enriched product data from CSV files into the database. "
            "By default, will NOT overwrite if data already exists. "
            "Use --force-reset to clear the table before populating."
        )
    )
    parser.add_argument(
        "--force-reset",
        action="store_true",
        help="Delete all existing enriched data before populating. "
             "If not set (default), only populates if the table is empty."
    )
    args = parser.parse_args()

    print("TimeL-E Enriched Data Populator")
    print("=" * 40)
    
    success = populate_enriched_data(force_reset=args.force_reset)
    
    if success:
        print("\nEnriched data population completed successfully!")
        print("Enriched product data can now be used in API calls.")
    else:
        print("\nEnriched data population failed!")
        sys.exit(1)
