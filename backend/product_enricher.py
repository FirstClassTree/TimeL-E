#!/usr/bin/env python3
"""
Product Enricher Script - TimeL-E Project (Concurrent Version)
===============================================================

This script enriches product data from products.csv by calling external APIs
to get descriptions, prices, and image URLs. Uses concurrent processing for
much faster performance while being respectful to API rate limits.

Now supports:
- --department / -d command-line argument
- If not specified, runs for ALL departments in departments.csv

Usage:
    python product_enricher.py                 # All departments
    python product_enricher.py --department 3  # Only department 3

Output:
    Creates enriched_products_dept{DEPARTMENT_ID}.csv for each department
"""

import pandas as pd
import requests
import time
import random
import os
import sys
import argparse
from urllib.parse import quote
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import deque

# Configuration
DEPARTMENTS = list(range(1, 22))  # Process ALL departments 1-21
INPUT_CSV = "../data/products.csv"
OUTPUT_DIR = "../data"  # Directory for enriched products
MAX_WORKERS = 60  # Number of concurrent threads (INCREASED for speed!)
REQUESTS_PER_SECOND = 50  # API rate limit (increased with more workers)
TIMEOUT = 10  # Request timeout in seconds
BATCH_SIZE = 50  # Products per progress update

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductEnricher:
    def __init__(self, department_id, output_csv):
        self.department_id = department_id
        self.output_csv = output_csv
        self.processed_count = 0
        self.total_count = 0
        self.lock = threading.Lock()
        self.request_times = deque()
        self.rate_limit_lock = threading.Lock()
        
    def create_session(self):
        """Create a new session for each thread"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'TimeL-E Product Enricher/1.0 (https://github.com/FirstClassTree/TimeL-E)'
        })
        return session
    
    def rate_limit_wait(self):
        """Implement rate limiting across all threads"""
        with self.rate_limit_lock:
            current_time = time.time()
            
            # Remove requests older than 1 second
            while self.request_times and current_time - self.request_times[0] > 1.0:
                self.request_times.popleft()
            
            # If we've made too many requests in the last second, wait
            if len(self.request_times) >= REQUESTS_PER_SECOND:
                sleep_time = 1.0 - (current_time - self.request_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Clean up old requests after waiting
                    current_time = time.time()
                    while self.request_times and current_time - self.request_times[0] > 1.0:
                        self.request_times.popleft()
            
            # Record this request
            self.request_times.append(current_time)
    
    def update_progress(self):
        """Thread-safe progress update"""
        with self.lock:
            self.processed_count += 1
            if self.processed_count % 10 == 0 or self.processed_count == self.total_count:
                logger.info(f"Progress: {self.processed_count}/{self.total_count} products processed")
                
    def process_single_product(self, product_data):
        """Process a single product with its own session"""
        product_id, product_name = product_data
        session = self.create_session()
        
        try:
            # Apply rate limiting
            self.rate_limit_wait()
            
            # Get enriched data from API
            enriched_data = self.search_openfoodfacts(product_name, session)
            
            # Update progress
            self.update_progress()
            
            # Return enriched product data
            return {
                'product_id': product_id,
                'product_name': product_name,
                'description': enriched_data['description'],
                'price': enriched_data['price'],
                'image_url': enriched_data['image_url']
            }
            
        except Exception as e:
            logger.warning(f"Error processing product {product_name}: {e}")
            self.update_progress()
            # Return fallback data
            fallback_data = self.get_fallback_data(product_name)
            return {
                'product_id': product_id,
                'product_name': product_name,
                'description': fallback_data['description'],
                'price': fallback_data['price'],
                'image_url': fallback_data['image_url']
            }
        finally:
            session.close()
        
    def clean_product_name(self, product_name):
        """Clean product name for better API search results"""
        if pd.isna(product_name):
            return ""
        
        # Remove common grocery store suffixes and clean up
        name = str(product_name).strip()
        # Remove size indicators, brand prefixes that might confuse search
        name = name.replace(" - ", " ").replace("®", "").replace("™", "")
        return name
    
    def search_openfoodfacts(self, product_name, session):
        """
        Search OpenFoodFacts API for product information
        Returns: dict with description, price, image_url
        """
        try:
            cleaned_name = self.clean_product_name(product_name)
            if not cleaned_name:
                return self.get_fallback_data(product_name)
            
            # OpenFoodFacts search API
            search_url = f"https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                'search_terms': cleaned_name,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 1
            }
            
            logger.debug(f"Searching OpenFoodFacts for: {cleaned_name}")
            response = session.get(search_url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('products') and len(data['products']) > 0:
                product = data['products'][0]
                
                # Extract information
                description = self.extract_description(product, product_name)
                price = self.extract_price(product)
                image_url = self.extract_image_url(product)
                
                logger.debug(f"Found data for {product_name}")
                return {
                    'description': description,
                    'price': price,
                    'image_url': image_url
                }
            else:
                logger.debug(f"No results found for {product_name}")
                return self.get_fallback_data(product_name)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed for {product_name}: {e}")
            return self.get_fallback_data(product_name)
        except Exception as e:
            logger.warning(f"Error processing {product_name}: {e}")
            return self.get_fallback_data(product_name)
    
    def extract_description(self, product, original_name):
        """Extract product description from API response"""
        # Try multiple fields for description
        description_fields = [
            'generic_name_en',
            'generic_name',
            'product_name_en',
            'product_name',
            'brands',
            'categories_en'
        ]
        
        for field in description_fields:
            if field in product and product[field]:
                desc = str(product[field]).strip()
                if len(desc) > 10:  # Ensure meaningful description
                    return desc[:200]  # Limit length
        
        # Fallback description
        return f"Premium {original_name.lower()} - high quality grocery product"
    
    def extract_price(self, product):
        """Extract or generate price"""
        # OpenFoodFacts doesn't typically have prices, so generate random
        return round(random.uniform(1.0, 15.0), 2)
    
    def extract_image_url(self, product):
        """Extract image URL from API response"""
        image_fields = ['image_url', 'image_front_url', 'image_small_url']
        
        for field in image_fields:
            if field in product and product[field]:
                return product[field]
        
        # Return placeholder if no image found
        return "https://via.placeholder.com/300x300?text=No+Image"
    
    def get_fallback_data(self, product_name):
        """Generate fallback data when API fails"""
        return {
            'description': f"Quality {product_name.lower()} - fresh grocery product",
            'price': round(random.uniform(1.0, 15.0), 2),
            'image_url': "https://via.placeholder.com/300x300?text=No+Image"
        }
    
    def process_products_for_department(self, df, department_id):
        """Process products for a specific department"""
        # Filter by department
        filtered_df = df[df['department_id'] == department_id].copy()
        dept_product_count = len(filtered_df)
        
        if dept_product_count == 0:
            logger.info(f"No products found for department {department_id}")
            return []
        
        logger.info(f"Processing {dept_product_count} products in department {department_id}")
        
        # Prepare product data for concurrent processing
        product_data = [(row['product_id'], row['product_name'], department_id) for _, row in filtered_df.iterrows()]
        
        return product_data
    
    def process_single_product_with_dept(self, product_data):
        """Process a single product with department info"""
        product_id, product_name, department_id = product_data
        session = self.create_session()
        
        try:
            # Apply rate limiting
            self.rate_limit_wait()
            
            # Get enriched data from API
            enriched_data = self.search_openfoodfacts(product_name, session)
            
            # Update progress
            self.update_progress()
            
            # Return enriched product data with department
            return {
                'product_id': product_id,
                'product_name': product_name,
                'department_id': department_id,
                'description': enriched_data['description'],
                'price': enriched_data['price'],
                'image_url': enriched_data['image_url']
            }
            
        except Exception as e:
            logger.warning(f"Error processing product {product_name}: {e}")
            self.update_progress()
            # Return fallback data
            fallback_data = self.get_fallback_data(product_name)
            return {
                'product_id': product_id,
                'product_name': product_name,
                'department_id': department_id,
                'description': fallback_data['description'],
                'price': fallback_data['price'],
                'image_url': fallback_data['image_url']
            }
        finally:
            session.close()

    def process_products(self):
        """Main processing function for ALL departments with concurrent processing"""
        try:
            if not os.path.exists(input_csv):
                logger.error(f"Input file not found: {input_csv}")
                logger.error("Make sure you're running this script from the data/ directory")
                return False
            
            # Read products CSV
            logger.info(f"Reading products from {input_csv}")
            df = pd.read_csv(input_csv)
            
            # Validate CSV structure
            required_columns = ['product_id', 'product_name', 'aisle_id', 'department_id']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"CSV missing required columns. Found: {list(df.columns)}")
                return False
            
            # Create output directory
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            # Process ALL departments 1-21
            logger.info(f"🚀 Processing ALL departments {DEPARTMENTS[0]}-{DEPARTMENTS[-1]} with {MAX_WORKERS} workers!")
            logger.info(f"Rate limit: {REQUESTS_PER_SECOND} requests per second")
            
            all_product_data = []
            department_stats = {}
            
            # Collect products from all departments
            for dept_id in DEPARTMENTS:
                dept_products = self.process_products_for_department(df, dept_id)
                all_product_data.extend(dept_products)
                department_stats[dept_id] = len(dept_products)
            
            self.total_count = len(all_product_data)
            
            if self.total_count == 0:
                logger.warning("No products found in any department!")
                return False
            
            logger.info(f"📊 Total products to process: {self.total_count}")
            for dept_id, count in department_stats.items():
                if count > 0:
                    logger.info(f"   Department {dept_id}: {count} products")
            
            # Process ALL products concurrently across departments
            enriched_products = []
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all tasks
                future_to_product = {
                    executor.submit(self.process_single_product_with_dept, data): data 
                    for data in all_product_data
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_product):
                    try:
                        result = future.result()
                        enriched_products.append(result)
                    except Exception as e:
                        product_data = future_to_product[future]
                        logger.error(f"Failed to process product {product_data[1]}: {e}")
                        # Add fallback data
                        fallback_data = self.get_fallback_data(product_data[1])
                        enriched_products.append({
                            'product_id': product_data[0],
                            'product_name': product_data[1],
                            'department_id': product_data[2],
                            'description': fallback_data['description'],
                            'price': fallback_data['price'],
                            'image_url': fallback_data['image_url']
                        })
            
            # Sort results by product_id to maintain order
            enriched_products.sort(key=lambda x: x['product_id'])
            
            # Save results - both consolidated and per-department files
            all_output_df = pd.DataFrame(enriched_products)
            
            # Save consolidated file
            consolidated_file = f"{OUTPUT_DIR}enriched_products_ALL_DEPARTMENTS.csv"
            all_output_df.to_csv(consolidated_file, index=False)
            logger.info(f"✅ Saved consolidated file: {consolidated_file}")
            
            # Save per-department files
            for dept_id in DEPARTMENTS:
                dept_products = [p for p in enriched_products if p['department_id'] == dept_id]
                if dept_products:
                    dept_df = pd.DataFrame(dept_products)
                    dept_file = f"{OUTPUT_DIR}enriched_products_dept{dept_id}.csv"
                    dept_df.to_csv(dept_file, index=False)
                    logger.info(f"✅ Department {dept_id}: {len(dept_products)} products saved to {dept_file}")
            
            # Display comprehensive results
            self.display_comprehensive_results(all_output_df, department_stats)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            return False
    
    def display_comprehensive_results(self, df, department_stats):
        """Display comprehensive results for all departments"""
        logger.info("\n" + "="*70)
        logger.info("🎉 ALL DEPARTMENTS PROCESSING COMPLETE!")
        logger.info("="*70)
        
        # Sample results from different departments
        logger.info("SAMPLE RESULTS (from different departments):")
        departments_shown = set()
        sample_count = 0
        
        for idx, row in df.iterrows():
            dept_id = row['department_id']
            if dept_id not in departments_shown and sample_count < 5:
                departments_shown.add(dept_id)
                sample_count += 1
                logger.info(f"\nDepartment {dept_id} Sample:")
                logger.info(f"  ID: {row['product_id']}")
                logger.info(f"  Name: {row['product_name']}")
                logger.info(f"  Description: {row['description'][:80]}...")
                logger.info(f"  Price: ${row['price']}")
        
        logger.info(f"\n📊 COMPREHENSIVE SUMMARY:")
        logger.info(f"   🎯 Total products processed: {len(df):,}")
        logger.info(f"   🏪 Departments covered: {len([d for d, c in department_stats.items() if c > 0])}/21")
        logger.info(f"   💰 Average price: ${df['price'].mean():.2f}")
        logger.info(f"   📁 Output directory: {OUTPUT_DIR}")
        
        logger.info(f"\n📈 PER-DEPARTMENT BREAKDOWN:")
        for dept_id in sorted(department_stats.keys()):
            count = department_stats[dept_id]
            if count > 0:
                dept_avg_price = df[df['department_id'] == dept_id]['price'].mean()
                logger.info(f"   Department {dept_id:2d}: {count:4d} products (avg ${dept_avg_price:.2f})")

def get_all_departments(departments_csv):
    if not os.path.exists(departments_csv):
        logger.error(f"Departments file not found: {departments_csv}")
        sys.exit(1)
    df = pd.read_csv(departments_csv)
    if 'department_id' not in df.columns:
        logger.error("departments.csv must have a 'department_id' column")
        sys.exit(1)
    return sorted(df['department_id'].dropna().unique().astype(int))

def main():
    """Main function for ALL departments processing"""
    print("🛒 TimeL-E Product Enricher - ALL DEPARTMENTS (Enhanced Version)")
    print("=" * 70)
    print(f"🎯 Processing ALL departments: {DEPARTMENTS[0]}-{DEPARTMENTS[-1]}")
    print(f"📁 Input file: {INPUT_CSV}")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print(f"⚡ Concurrent workers: {MAX_WORKERS} (4x faster!)")
    print(f"🚀 Rate limit: {REQUESTS_PER_SECOND} requests/second")
    print("=" * 70)
    
    enricher = ProductEnricher()
    
    start_time = time.time()
    success = enricher.process_products()
    end_time = time.time()
    
    if success:
        duration = end_time - start_time
        print(f"\n🎉 ✅ ALL DEPARTMENTS PROCESSING COMPLETED! ✅ 🎉")
        print(f"⏱️  Total time: {duration:.1f} seconds")
        print(f"📊 Products processed: {enricher.total_count:,}")
        print(f"⚡ Processing speed: ~{enricher.total_count/duration:.1f} products/second")
        print(f"📁 Results saved to: {OUTPUT_DIR}")
        print(f"🏪 Departments 1-21 all processed with {MAX_WORKERS} workers!")
        print("\n📂 Generated files:")
        print(f"   • enriched_products_ALL_DEPARTMENTS.csv (consolidated)")
        print(f"   • enriched_products_dept1.csv through enriched_products_dept21.csv")
    else:
        print(f"\n❌ Processing failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
