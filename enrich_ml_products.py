#!/usr/bin/env python3
"""
Smart ML Product Enricher Script
================================

This script adds enriched product data for ML predictions to enriched_products_dept1.csv
Only adds products that don't already exist (avoids duplicates).

Usage: python enrich_ml_products.py
"""

import csv
import os
import random

# Configuration
CSV_FILE = "db_service/data/enriched_products_dept1.csv"

# ML Prediction Products to enrich
ML_PRODUCTS = [
    {"product_id": 2716, "product_name": "Organic Greek Lowfat Yogurt With Strawberries"},
    {"product_id": 2962, "product_name": "Milk, Reduced Fat, 2% Milkfat"},
    {"product_id": 3957, "product_name": "100% Raw Coconut Water"},
    {"product_id": 5876, "product_name": "Organic Lemon"},
    {"product_id": 8379, "product_name": "Wild Smoked Sockeye Salmon"},
    {"product_id": 11512, "product_name": "Honey Yoghurt"},
    {"product_id": 11937, "product_name": "Mixed Berries"},
    {"product_id": 23986, "product_name": "Grassfed Whole Milk Plain Yogurt"},
    {"product_id": 24852, "product_name": "Banana"},
    {"product_id": 25640, "product_name": "White Peach"},
    {"product_id": 45210, "product_name": "Organic Greek Lowfat Yogurt With Blueberries"},
    {"product_id": 45445, "product_name": "Organic Bagged Mini Dark Peanut Butter"},
    {"product_id": 47029, "product_name": "Organic Greek Nonfat Yogurt With Mixed Berries"},
    {"product_id": 48726, "product_name": "Organic Nonfat Greek Yogurt With Peaches"},
    {"product_id": 49247, "product_name": "Coconut Yoghurt"},
    {"product_id": 49374, "product_name": "Organic Cultured Cream Cheese Spread"},
    {"product_id": 49628, "product_name": "Yoghurt Blueberry"}
]

def generate_realistic_price(product_name):
    """Generate realistic prices based on product type"""
    name_lower = product_name.lower()
    
    if any(word in name_lower for word in ['salmon', 'smoked']):
        return round(random.uniform(10.0, 15.0), 2)
    elif any(word in name_lower for word in ['peanut butter', 'spread']):
        return round(random.uniform(6.0, 9.0), 2)
    elif any(word in name_lower for word in ['berries', 'mixed']):
        return round(random.uniform(5.0, 7.0), 2)
    elif any(word in name_lower for word in ['yogurt', 'yoghurt']):
        return round(random.uniform(4.0, 6.0), 2)
    elif any(word in name_lower for word in ['coconut water']):
        return round(random.uniform(3.0, 5.0), 2)
    elif any(word in name_lower for word in ['milk']):
        return round(random.uniform(3.0, 4.5), 2)
    elif any(word in name_lower for word in ['peach', 'white peach']):
        return round(random.uniform(2.0, 4.0), 2)
    elif any(word in name_lower for word in ['banana']):
        return round(random.uniform(1.0, 2.0), 2)
    elif any(word in name_lower for word in ['lemon']):
        return round(random.uniform(0.5, 1.5), 2)
    else:
        return round(random.uniform(2.0, 8.0), 2)

def generate_description(product_name):
    """Generate quality description following the format"""
    return f"Quality {product_name.lower()} - fresh grocery product"

def get_existing_product_ids(csv_file):
    """Read existing product IDs from CSV file"""
    existing_ids = set()
    
    if not os.path.exists(csv_file):
        print(f"⚠️  CSV file {csv_file} not found. Will create new file.")
        return existing_ids
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'product_id' in row and row['product_id']:
                    existing_ids.add(int(row['product_id']))
    except Exception as e:
        print(f"⚠️  Error reading CSV file: {e}")
    
    return existing_ids

def append_products_to_csv(csv_file, products_to_add):
    """Append new products to CSV file"""
    if not products_to_add:
        print("✅ No new products to add.")
        return
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    # Check if file exists and has header
    file_exists = os.path.exists(csv_file)
    write_header = not file_exists
    
    if file_exists:
        # Check if file is empty or has no header
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            content = file.read().strip()
            if not content or not content.startswith('product_id'):
                write_header = True
    
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['product_id', 'product_name', 'description', 'price', 'image_url']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if write_header:
                writer.writeheader()
            
            for product in products_to_add:
                writer.writerow(product)
        
        print(f"✅ Successfully added {len(products_to_add)} products to {csv_file}")
        
    except Exception as e:
        print(f"❌ Error writing to CSV file: {e}")

def main():
    print("🛒 Smart ML Product Enricher")
    print("=" * 40)
    print(f"Target file: {CSV_FILE}")
    print(f"Products to check: {len(ML_PRODUCTS)}")
    print("=" * 40)
    
    # Get existing product IDs
    existing_ids = get_existing_product_ids(CSV_FILE)
    print(f"📊 Found {len(existing_ids)} existing products in CSV")
    
    # Determine which products need to be added
    products_to_add = []
    
    for product in ML_PRODUCTS:
        product_id = product["product_id"]
        product_name = product["product_name"]
        
        if product_id in existing_ids:
            print(f"⏭️  Product {product_id} ({product_name[:30]}...) already exists - skipping")
        else:
            # Generate enriched data
            enriched_product = {
                'product_id': product_id,
                'product_name': product_name,
                'description': generate_description(product_name),
                'price': generate_realistic_price(product_name),
                'image_url': 'https://via.placeholder.com/300x300?text=No+Image'
            }
            products_to_add.append(enriched_product)
            print(f"➕ Will add Product {product_id} ({product_name[:30]}...) - ${enriched_product['price']}")
    
    print("=" * 40)
    print(f"📋 Summary: {len(products_to_add)} new products to add")
    
    if products_to_add:
        # Add new products to CSV
        append_products_to_csv(CSV_FILE, products_to_add)
        
        print("\n🎉 Enrichment completed!")
        print(f"📁 Updated file: {CSV_FILE}")
        print(f"✨ Added {len(products_to_add)} new enriched products")
        
        # Show sample of added products
        print("\n📋 Sample of added products:")
        for i, product in enumerate(products_to_add[:3]):
            print(f"  {i+1}. {product['product_id']} - {product['product_name'][:40]}... - ${product['price']}")
        
        if len(products_to_add) > 3:
            print(f"  ... and {len(products_to_add) - 3} more products")
    
    else:
        print("\n✅ All ML prediction products already exist in the CSV file!")
        print("🎯 No action needed - your enriched data is up to date.")

if __name__ == "__main__":
    main()
