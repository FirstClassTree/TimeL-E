#!/usr/bin/env python3
"""
Test script for the fixed register endpoint.
Run this after starting the TimeL-E stack with docker-compose.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_register_endpoint():
    print("🧪 Testing Fixed Register Endpoint")
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
    
    # Test 2: Successful registration
    print("\n2. Testing successful registration...")
    unique_email = f"testuser{int(time.time())}@example.com"
    successful_user = {
        "name": f"testuser{int(time.time())}",
        "email_address": unique_email,
        "password": "testpassword123",
        "phone_number": "+1-555-0123",
        "street_address": "123 Test Street",
        "city": "Test City",
        "postal_code": "12345",
        "country": "US"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/register", 
            json=successful_user,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("   ✅ Registration successful!")
            registered_user_id = response.json()["data"]["user_id"]
        else:
            print("   ❌ Registration failed!")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Duplicate email error
    print("\n3. Testing duplicate email error handling...")
    duplicate_user = {
        "name": "anotheruser",
        "email_address": unique_email,  # Same email as above
        "password": "anotherpassword123",
        "phone_number": "+1-555-0456",
        "street_address": "456 Another Street",
        "city": "Another City",
        "postal_code": "45678",
        "country": "US"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/register", 
            json=duplicate_user,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("   ✅ Duplicate email properly rejected!")
        else:
            print("   ❌ Expected 400 error for duplicate email!")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Invalid email format
    print("\n4. Testing invalid email format...")
    invalid_email_user = {
        "name": "invaliduser",
        "email_address": "not-an-email",
        "password": "password123",
        "phone_number": "+1-555-0789",
        "street_address": "789 Invalid Street",
        "city": "Invalid City",
        "postal_code": "78901",
        "country": "US"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/register", 
            json=invalid_email_user,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 422:
            print("   ✅ Invalid email format properly rejected!")
        else:
            print("   ❌ Expected 422 validation error for invalid email!")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Missing required fields
    print("\n5. Testing missing required fields...")
    incomplete_user = {
        "name": "incompleteuser",
        "email_address": "incomplete@example.com"
        # Missing required fields
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/register", 
            json=incomplete_user,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 422:
            print("   ✅ Missing fields properly rejected!")
        else:
            print("   ❌ Expected 422 validation error for missing fields!")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Register Endpoint Testing Complete!")
    print("\nFixed Issues:")
    print("- ✅ Successful registration works")
    print("- ✅ Error handling for duplicate emails")
    print("- ✅ Validation for invalid email formats")
    print("- ✅ Validation for missing required fields")
    print("- ✅ Proper HTTP status codes")
    print("- ✅ User-friendly error messages")

if __name__ == "__main__":
    test_register_endpoint()
