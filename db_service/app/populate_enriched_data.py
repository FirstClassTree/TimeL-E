#!/usr/bin/env python3
"""
Populate enriched product data from CSV file
"""

import pandas as pd
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.models.products import ProductEnriched

def populate_enriched_data():
    """Populate the product_enriched table from CSV"""
    
    # Database setup
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Use /data/products_enriched/ (/data is a mounted volume)
    enriched_dir = Path("/data/products_enriched")
    csv_files = sorted(enriched_dir.glob("enriched_products_dept*.csv"))
    
    if not csv_files:
        print(f"Error: No enriched CSV files found in {enriched_dir}")
        print("Make sure enriched data was generated using the product_enricher.py script and that /data is mounted correctly")
        return False
    else:
        print(f"Found enriched CSV files: {[str(f) for f in csv_files]}")

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
        
        # Create database session
        session = SessionLocal()
        
        try:
            print("Clearing existing enriched data...")
            session.execute(text("DELETE FROM products.product_enriched"))
            session.commit()
            
            print("Inserting enriched product data...")
            
            success_count = 0
            error_count = 0
            
            for _, row in combined_df.iterrows():
                try:
                    enriched = ProductEnriched(
                        product_id=int(row['product_id']),
                        description=row['description'] if pd.notna(row['description']) else None,
                        price=float(row['price']) if pd.notna(row['price']) else None,
                        image_url=row['image_url'] if pd.notna(row['image_url']) else None
                    )
                    
                    session.add(enriched)
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        print(f"   Processed {success_count} products...")
                        
                except Exception as e:
                    error_count += 1
                    print(f"   Warning: Failed to insert product {row['product_id']}: {e}")
                    continue

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
            return False
            
        finally:
            session.close()
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False

def main():
    print("TimeL-E Enriched Data Populator")
    print("=" * 40)
    
    success = populate_enriched_data()
    
    if success:
        print("\nEnriched data population completed successfully!")
        print("Enriched product data can now be used in API calls.")
    else:
        print("\nEnriched data population failed!")
        sys.exit(1)

