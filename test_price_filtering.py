#!/usr/bin/env python3
"""
Test script for the new price filtering functionality in the products API
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/products"

def test_price_filtering():
    """Test various price filtering scenarios"""
    
    print("🧪 Testing Price Filtering Functionality\n")
    
    test_cases = [
        {
            "name": "Original request - minPrice=0, maxPrice=300",
            "url": f"{BASE_URL}/?limit=5&minPrice=0&maxPrice=300"
        },
        {
            "name": "Price range 10-15",
            "url": f"{BASE_URL}/?limit=5&minPrice=10&maxPrice=15"
        },
        {
            "name": "Only minimum price (minPrice=20)",
            "url": f"{BASE_URL}/?limit=5&minPrice=20"
        },
        {
            "name": "Only maximum price (maxPrice=3)",
            "url": f"{BASE_URL}/?limit=5&maxPrice=3"
        },
        {
            "name": "No price filters (baseline)",
            "url": f"{BASE_URL}/?limit=5"
        }
    ]
    
    for test_case in test_cases:
        print(f"🔍 {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            response = requests.get(test_case['url'])
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success'):
                products = data['data']['products']
                print(f"   ✅ Success: {len(products)} products returned")
                
                if products:
                    prices = [p['price'] for p in products if p['price'] is not None]
                    if prices:
                        print(f"   💰 Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                    else:
                        print(f"   💰 No priced products in results")
                else:
                    print(f"   💰 No products found")
            else:
                print(f"   ❌ Failed: {data.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        print()

if __name__ == "__main__":
    test_price_filtering()
