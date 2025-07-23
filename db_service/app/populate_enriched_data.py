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
from app.db_core.config import settings
from app.db_core.models.products import ProductEnriched
from app.db_core.database import SessionLocal

def populate_enriched_data(force_reset=False):
    """Populate the product_enriched table from CSV"""

    # Use /data/products_enriched/ (/data is a mounted volume)
    enriched_dir = Path("/data/products_enriched")
    csv_files = sorted(enriched_dir.glob("enriched_products_dept*.csv"))
    
    if not csv_files:
        print(f"Error: No enriched CSV files found in {enriched_dir}")
        print("Make sure enriched data was generated using the product_enricher.py script and that /data is mounted correctly")
        return False
    else:
        print(f"Found enriched CSV files: {[str(f) for f in csv_files]}")


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

        BATCH_SIZE = 200  # tune this as needed

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
                error_count += len(objects)
                print(f"   ERROR: Batch insert failed: {batch_err} (will try individual rows)")
                # Fallback: try each row individually
                for obj in objects:
                    try:
                        session.add(obj)
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

        return True

    except Exception as e:
        session.rollback()
        print(f"Error during database operations: {e}")
        # traceback.print_exc()
        return False

    finally:
        session.close()


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
