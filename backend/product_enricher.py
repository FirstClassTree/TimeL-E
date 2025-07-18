#!/usr/bin/env python3
"""
Product Enricher Script - TimeL-E Project (Concurrent Version)
===============================================================

This script enriches product data from products.csv by calling external APIs
to get descriptions, prices, and image URLs. Uses concurrent processing for
much faster performance while being respectful to API rate limits.

Usage:
    python product_enricher.py

Output:
    Creates data/enriched_products_dept{DEPARTMENT_ID}.csv

Author: TimeL-E Team
"""

import pandas as pd
import requests
import time
import random
import os
import sys
from urllib.parse import quote
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import deque

# Configuration
DEPARTMENT_ID = 1  # Change this to process different departments
INPUT_CSV = "../data/products.csv"
OUTPUT_CSV = f"../data/enriched_products_dept{DEPARTMENT_ID}.csv"
MAX_WORKERS = 15  # Number of concurrent threads
REQUESTS_PER_SECOND = 10  # API rate limit (requests per second)
TIMEOUT = 10  # Request timeout in seconds
BATCH_SIZE = 50  # Products per progress update

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductEnricher:
    def __init__(self):
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
    
    def process_products(self):
        """Main processing function with concurrent processing"""
        try:
            # Check if input file exists
            if not os.path.exists(INPUT_CSV):
                logger.error(f"Input file not found: {INPUT_CSV}")
                logger.error("Make sure you're running this script from the backend/ directory")
                return False
            
            # Read products CSV
            logger.info(f"Reading products from {INPUT_CSV}")
            df = pd.read_csv(INPUT_CSV)
            
            # Validate CSV structure
            required_columns = ['product_id', 'product_name', 'aisle_id', 'department_id']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"CSV missing required columns. Found: {list(df.columns)}")
                return False
            
            # Filter by department
            filtered_df = df[df['department_id'] == DEPARTMENT_ID].copy()
            self.total_count = len(filtered_df)
            
            if self.total_count == 0:
                logger.warning(f"No products found for department_id = {DEPARTMENT_ID}")
                return False
            
            logger.info(f"Found {self.total_count} products in department {DEPARTMENT_ID}")
            logger.info(f"Using {MAX_WORKERS} concurrent workers for processing")
            logger.info(f"Rate limit: {REQUESTS_PER_SECOND} requests per second")
            
            # Prepare product data for concurrent processing
            product_data = [(row['product_id'], row['product_name']) for _, row in filtered_df.iterrows()]
            
            # Process products concurrently
            enriched_products = []
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all tasks
                future_to_product = {
                    executor.submit(self.process_single_product, data): data 
                    for data in product_data
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
                            'description': fallback_data['description'],
                            'price': fallback_data['price'],
                            'image_url': fallback_data['image_url']
                        })
            
            # Sort results by product_id to maintain order
            enriched_products.sort(key=lambda x: x['product_id'])
            
            # Save results
            output_df = pd.DataFrame(enriched_products)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
            
            output_df.to_csv(OUTPUT_CSV, index=False)
            logger.info(f"✅ Successfully saved {len(enriched_products)} enriched products to {OUTPUT_CSV}")
            
            # Display sample results
            self.display_sample_results(output_df)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            return False
    
    def display_sample_results(self, df):
        """Display sample results for verification"""
        logger.info("\n" + "="*60)
        logger.info("SAMPLE RESULTS (first 3 products):")
        logger.info("="*60)
        
        for idx in range(min(3, len(df))):
            row = df.iloc[idx]
            logger.info(f"\nProduct {idx + 1}:")
            logger.info(f"  ID: {row['product_id']}")
            logger.info(f"  Name: {row['product_name']}")
            logger.info(f"  Description: {row['description'][:100]}...")
            logger.info(f"  Price: ${row['price']}")
            logger.info(f"  Image: {row['image_url'][:50]}...")
        
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Total products processed: {len(df)}")
        logger.info(f"   Department: {DEPARTMENT_ID}")
        logger.info(f"   Output file: {OUTPUT_CSV}")
        logger.info(f"   Average price: ${df['price'].mean():.2f}")

def main():
    """Main function"""
    print("🛒 TimeL-E Product Enricher (Concurrent Version)")
    print("=" * 50)
    print(f"Processing department: {DEPARTMENT_ID}")
    print(f"Input file: {INPUT_CSV}")
    print(f"Output file: {OUTPUT_CSV}")
    print(f"Concurrent workers: {MAX_WORKERS}")
    print(f"Rate limit: {REQUESTS_PER_SECOND} requests/second")
    print("=" * 50)
    
    enricher = ProductEnricher()
    
    start_time = time.time()
    success = enricher.process_products()
    end_time = time.time()
    
    if success:
        duration = end_time - start_time
        print(f"\n✅ Processing completed in {duration:.1f} seconds")
        print(f"📁 Results saved to: {OUTPUT_CSV}")
        print(f"⚡ Speed: ~{enricher.total_count/duration:.1f} products/second")
        print(f"\n💡 To process other departments, change DEPARTMENT_ID and run again")
    else:
        print(f"\n❌ Processing failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
