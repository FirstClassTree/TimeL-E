#!/usr/bin/env python3
"""
Test script for the simplified orders API endpoints.
Run this after starting the full TimeL-E stack with docker-compose.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_simplified_orders_api():
    print("🧪 Testing Simplified Orders API")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Connection error: {e}")
        print("   Make sure the backend is running!")
        return
    
    # Test 2: Get user orders (empty case)
    print("\n2. Testing GET /api/orders/user/999 (non-existent user)...")
    try:
        response = requests.get(f"{BASE_URL}/api/orders/user/999?limit=5&offset=0")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get user orders (existing user - if any)
    print("\n3. Testing GET /api/orders/user/1 (potentially existing user)...")
    try:
        response = requests.get(f"{BASE_URL}/api/orders/user/1?limit=5&offset=0")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Create order (will need valid user and products)
    print("\n4. Testing POST /api/orders/ (will test validation)...")
    test_order = {
        "user_id": 1,
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orders/", 
            json=test_order,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Simplified Orders API Testing Complete!")
    print("\nNew simplified API endpoints:")
    print("- GET /api/orders/user/{user_id}?limit={limit}&offset={offset}")
    print("- POST /api/orders/ (with user_id and items)")
    print("\nRemoved complex endpoints:")
    print("- All tracking, delivery, invoice endpoints")
    print("- Individual order management endpoints")
    print("- Order item management endpoints")

if __name__ == "__main__":
    test_simplified_orders_api()
