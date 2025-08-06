#!/usr/bin/env python3
"""
Test script for backend cart endpoints
Tests all CRUD operations with integer user IDs
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/cart"
TEST_USER_ID = "73662"  # Known user with existing cart
EMPTY_USER_ID = "201520"  # Known user without cart
TEST_PRODUCT_ID = 4

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make HTTP request and return JSON response"""
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else {},
            "success": 200 <= response.status_code < 300
        }
    except Exception as e:
        return {
            "status_code": 0,
            "response": {"error": str(e)},
            "success": False
        }

def test_get_cart_with_items():
    """Test GET /cart/{user_id} - user with existing cart"""
    print("🧪 Testing GET cart with items...")
    result = make_request("GET", TEST_USER_ID)
    
    if result["success"]:
        data = result["response"].get("data", {})
        if data.get("items") and len(data["items"]) > 0:
            print(f"✅ SUCCESS: Found cart with {len(data['items'])} items")
            print(f"   Cart ID: {data.get('cartId')}")
            print(f"   User ID: {data.get('userId')}")
            return True
        else:
            print("⚠️  Cart found but no items")
            return True
    else:
        print(f"❌ FAILED: {result}")
        return False

def test_get_empty_cart():
    """Test GET /cart/{user_id} - user without cart"""
    print("\n🧪 Testing GET empty cart...")
    result = make_request("GET", EMPTY_USER_ID)
    
    if result["success"]:
        data = result["response"].get("data", {})
        if data.get("totalItems", 0) == 0:
            print("✅ SUCCESS: Empty cart returned correctly")
            return True
        else:
            print(f"⚠️  Expected empty cart but got {data.get('totalItems', 0)} items")
            return False
    else:
        print(f"❌ FAILED: {result}")
        return False

def test_add_item_to_cart():
    """Test POST /cart/{user_id}/items - add item to cart"""
    print("\n🧪 Testing ADD item to cart...")
    data = {
        "productId": TEST_PRODUCT_ID,
        "quantity": 2
    }
    result = make_request("POST", f"{EMPTY_USER_ID}/items", data)
    
    if result["success"]:
        response_data = result["response"].get("data", {})
        items = response_data.get("items", [])
        if len(items) > 0 and items[0]["productId"] == TEST_PRODUCT_ID:
            print(f"✅ SUCCESS: Added product {TEST_PRODUCT_ID} to cart")
            print(f"   Product: {items[0].get('productName')}")
            print(f"   Quantity: {items[0].get('quantity')}")
            return True
        else:
            print("❌ FAILED: Item not found in cart after adding")
            return False
    else:
        print(f"❌ FAILED: {result}")
        return False

def test_update_cart_item():
    """Test PUT /cart/{user_id}/items/{product_id} - update item quantity"""
    print("\n🧪 Testing UPDATE cart item...")
    data = {"quantity": 5}
    result = make_request("PUT", f"{EMPTY_USER_ID}/items/{TEST_PRODUCT_ID}", data)
    
    if result["success"]:
        response_data = result["response"].get("data", {})
        items = response_data.get("items", [])
        if len(items) > 0 and items[0]["quantity"] == 5:
            print("✅ SUCCESS: Updated item quantity to 5")
            return True
        else:
            print(f"❌ FAILED: Expected quantity 5, got {items[0].get('quantity') if items else 'no items'}")
            return False
    else:
        print(f"❌ FAILED: {result}")
        return False

def test_remove_cart_item():
    """Test DELETE /cart/{user_id}/items/{product_id} - remove item"""
    print("\n🧪 Testing REMOVE cart item...")
    result = make_request("DELETE", f"{EMPTY_USER_ID}/items/{TEST_PRODUCT_ID}")
    
    if result["success"]:
        response_data = result["response"].get("data", {})
        total_items = response_data.get("totalItems", 0)
        if total_items == 0:
            print("✅ SUCCESS: Item removed, cart is now empty")
            return True
        else:
            print(f"❌ FAILED: Expected 0 items, got {total_items}")
            return False
    else:
        print(f"❌ FAILED: {result}")
        return False

def test_invalid_user():
    """Test with invalid user ID"""
    print("\n🧪 Testing INVALID user ID...")
    result = make_request("GET", "999999")
    
    if not result["success"] and result["status_code"] >= 400:
        print("✅ SUCCESS: Invalid user ID properly rejected")
        return True
    else:
        print(f"❌ FAILED: Expected error for invalid user, got: {result}")
        return False

def main():
    """Run all cart endpoint tests"""
    print("🚀 Starting Backend Cart Endpoint Tests")
    print("=" * 50)
    
    tests = [
        test_get_cart_with_items,
        test_get_empty_cart,
        test_add_item_to_cart,
        test_update_cart_item,
        test_remove_cart_item,
        test_invalid_user
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Backend cart endpoints are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
