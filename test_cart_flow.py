#!/usr/bin/env python3
"""
Simple test script to verify the add to cart flow is working end-to-end.
This tests the critical path: Frontend -> Backend -> DB Service -> Database
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:8000"
DB_SERVICE_URL = "http://localhost:7000"
API_PREFIX = "/api/v1"

def test_add_to_cart_flow():
    """Test the complete add to cart flow"""
    print("🧪 Testing Add to Cart End-to-End Flow")
    print("=" * 50)
    
    # Test data
    test_user_id = "1"  # Using simple integer user ID
    test_product_id = 1
    test_quantity = 2
    
    try:
        # Step 1: Test Backend Health
        print("1️⃣  Testing Backend Health...")
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code != 200:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
        print("✅ Backend is healthy")
        
        # Step 2: Test DB Service Health  
        print("2️⃣  Testing DB Service Health...")
        response = requests.get(f"{DB_SERVICE_URL}/health")
        if response.status_code != 200:
            print(f"❌ DB Service health check failed: {response.status_code}")
            return False
        print("✅ DB Service is healthy")
        
        # Step 3: Test Add to Cart via Backend
        print("3️⃣  Testing Add to Cart...")
        cart_data = {
            "productId": test_product_id,
            "quantity": test_quantity
        }
        
        response = requests.post(
            f"{BACKEND_URL}{API_PREFIX}/cart/{test_user_id}/items",
            json=cart_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Add to cart failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        cart_response = response.json()
        print("✅ Add to cart successful")
        print(f"Response: {json.dumps(cart_response, indent=2)}")
        
        # Step 4: Verify Cart Contents
        print("4️⃣  Verifying Cart Contents...")
        response = requests.get(f"{BACKEND_URL}{API_PREFIX}/cart/{test_user_id}")
        
        if response.status_code != 200:
            print(f"❌ Get cart failed: {response.status_code}")
            return False
            
        cart_data = response.json()
        print("✅ Cart retrieved successfully")
        
        # Check if item is in cart
        if cart_data.get("data", {}).get("items"):
            items = cart_data["data"]["items"]
            found_item = None
            for item in items:
                if item.get("productId") == test_product_id:
                    found_item = item
                    break
                    
            if found_item:
                print(f"✅ Product {test_product_id} found in cart with quantity {found_item.get('quantity')}")
                if found_item.get("quantity") >= test_quantity:
                    print("✅ Correct quantity in cart")
                else:
                    print(f"⚠️  Expected quantity {test_quantity}, got {found_item.get('quantity')}")
            else:
                print(f"❌ Product {test_product_id} not found in cart")
                return False
        else:
            print("❌ Cart is empty or invalid response")
            return False
            
        print("\n🎉 Add to Cart End-to-End Test PASSED!")
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure services are running: docker-compose up")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_cart_api_direct():
    """Test cart API directly via db-service"""
    print("\n🔧 Testing Cart API via DB Service...")
    print("=" * 40)
    
    test_user_id = "1"
    test_product_id = 1
    test_quantity = 1
    
    try:
        # Test add item directly to db-service
        cart_data = {
            "product_id": test_product_id,
            "quantity": test_quantity
        }
        
        response = requests.post(
            f"{DB_SERVICE_URL}/carts/{test_user_id}/items",
            json=cart_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ DB Service add to cart failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        print("✅ DB Service add to cart successful")
        return True
        
    except Exception as e:
        print(f"❌ DB Service test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Cart Functionality Test Suite")
    print("=" * 60)
    
    # Run tests
    backend_success = test_add_to_cart_flow()
    db_service_success = test_cart_api_direct()
    
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    print(f"Backend E2E Test: {'✅ PASS' if backend_success else '❌ FAIL'}")
    print(f"DB Service Test:  {'✅ PASS' if db_service_success else '❌ FAIL'}")
    
    if backend_success and db_service_success:
        print("\n🎉 All tests passed! Add to cart should work in frontend.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
        sys.exit(1)
