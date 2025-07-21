#!/usr/bin/env python3
"""
Test enriched product API endpoints
"""

import requests
import json
import sys

def test_db_service():
    """Test db-service directly"""
    print("🧪 Testing DB Service...")
    try:
        response = requests.get("http://localhost:7000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ DB Service is healthy")
            return True
        else:
            print(f"   ❌ DB Service unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ DB Service not reachable: {e}")
        return False

def test_backend_api():
    """Test backend API"""
    print("🧪 Testing Backend API...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend API is healthy")
            return True
        else:
            print(f"   ❌ Backend API unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend API not reachable: {e}")
        return False

def test_enriched_products():
    """Test products endpoint for enriched data"""
    print("🧪 Testing Enriched Product Data...")
    
    try:
        # Test DB service products endpoint directly
        print("   Testing DB Service /products endpoint...")
        response = requests.get("http://localhost:7000/products?limit=5", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            if products:
                print(f"   ✅ Found {len(products)} products")
                
                # Check if any products have enriched data
                enriched_count = 0
                for product in products:
                    if any(product.get(field) is not None for field in ['description', 'price', 'image_url']):
                        enriched_count += 1
                
                print(f"   📊 Products with enriched data: {enriched_count}/{len(products)}")
                
                # Show sample product
                sample = products[0]
                print(f"   📦 Sample product:")
                print(f"      ID: {sample.get('product_id')}")
                print(f"      Name: {sample.get('product_name')}")
                print(f"      Department: {sample.get('department_name')}")
                print(f"      Description: {sample.get('description', 'None')}")
                print(f"      Price: ${sample.get('price', 'None')}")
                print(f"      Image: {sample.get('image_url', 'None')}")
                
                return True
            else:
                print("   ❌ No products found")
                return False
        else:
            print(f"   ❌ DB Service products endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing products: {e}")
        return False

def test_backend_products():
    """Test backend API products endpoint"""
    print("🧪 Testing Backend Products API...")
    
    try:
        response = requests.get("http://localhost:8000/api/products/?limit=3", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                products = data.get('data', {}).get('products', [])
                print(f"   ✅ Backend API returned {len(products)} products")
                
                if products:
                    # Check enriched data in backend response
                    enriched_count = 0
                    for product in products:
                        if any(product.get(field) is not None for field in ['description', 'price', 'image_url']):
                            enriched_count += 1
                    
                    print(f"   📊 Products with enriched data: {enriched_count}/{len(products)}")
                    
                    # Show sample
                    sample = products[0]
                    print(f"   📦 Sample backend product:")
                    print(f"      ID: {sample.get('product_id')}")
                    print(f"      Name: {sample.get('product_name')}")
                    print(f"      Description: {sample.get('description', 'None')}")
                    print(f"      Price: ${sample.get('price', 'None')}")
                    
                return True
            else:
                print(f"   ❌ Backend API returned error: {data.get('message')}")
                return False
        else:
            print(f"   ❌ Backend products endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing backend products: {e}")
        return False

def main():
    print("🛒 TimeL-E Enriched Product API Test")
    print("=" * 40)
    
    tests = [
        test_db_service,
        test_backend_api,
        test_enriched_products,
        test_backend_products
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"✅ Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! Enriched product integration is working!")
    else:
        print("💥 Some tests failed. Check the output above for details.")
        print("\n💡 Make sure to run: docker-compose up --build")

if __name__ == "__main__":
    main()
