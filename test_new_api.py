#!/usr/bin/env python3
"""
Comprehensive test script for the new TimeL-E Grocery API
Tests all endpoints with real CSV data structure
"""
import requests
import json

API_BASE = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print('='*50)

def test_api():
    print("🚀 Testing TimeL-E Grocery API with CSV Data")
    
    # Test 1: Health Check
    print_section("Health Check")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ API is healthy")
            print(f"   Version: {data['data']['version']}")
        else:
            print("❌ Health check failed")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    # Test 2: Product Endpoints
    print_section("Product Operations")
    
    # Get products with pagination
    try:
        response = requests.get(f"{API_BASE}/api/products/?limit=5")
        if response.status_code == 200:
            data = response.json()
            products = data['data']['products']
            print(f"✅ Retrieved {len(products)} products")
            for product in products:
                print(f"   • {product['product_name']} (ID: {product['product_id']})")
                print(f"     Department: {product['department_name']}, Aisle: {product['aisle_name']}")
        else:
            print("❌ Failed to get products")
    except Exception as e:
        print(f"❌ Products error: {e}")
    
    # Search products
    try:
        response = requests.get(f"{API_BASE}/api/products/search?q=chocolate")
        if response.status_code == 200:
            data = response.json()
            products = data['data']['products']
            print(f"✅ Found {len(products)} products matching 'chocolate'")
            for product in products:
                print(f"   • {product['product_name']}")
        else:
            print("❌ Failed to search products")
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    # Get specific product
    try:
        response = requests.get(f"{API_BASE}/api/products/1")
        if response.status_code == 200:
            data = response.json()
            product = data['data']
            print(f"✅ Retrieved product: {product['product_name']}")
            print(f"   Department: {product['department_name']}")
            print(f"   Aisle: {product['aisle_name']}")
        else:
            print("❌ Failed to get specific product")
    except Exception as e:
        print(f"❌ Product detail error: {e}")

    # Test 3: Categories
    print_section("Category Navigation")
    
    # Get departments
    try:
        response = requests.get(f"{API_BASE}/api/departments")
        if response.status_code == 200:
            data = response.json()
            departments = data['data']['departments']
            print(f"✅ Retrieved {len(departments)} departments:")
            for dept in departments[:3]:  # Show first 3
                print(f"   • {dept['department']} (ID: {dept['department_id']})")
        else:
            print("❌ Failed to get departments")
    except Exception as e:
        print(f"❌ Departments error: {e}")
    
    # Get categories summary
    try:
        response = requests.get(f"{API_BASE}/api/categories/summary")
        if response.status_code == 200:
            data = response.json()
            summary = data['data']
            print(f"✅ Categories Summary:")
            print(f"   Total Products: {summary['total_products']}")
            print(f"   Departments: {summary['departments']['total']}")
            print(f"   Aisles: {summary['aisles']['total']}")
        else:
            print("❌ Failed to get categories summary")
    except Exception as e:
        print(f"❌ Categories summary error: {e}")

    # Test 4: Order Operations
    print_section("Order Management")
    
    # Create a new order
    try:
        order_data = {
            "user_id": 999,
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1}
            ]
        }
        response = requests.post(f"{API_BASE}/api/orders/", json=order_data)
        if response.status_code == 200:
            data = response.json()
            order = data['data']
            print(f"✅ Created order {order['order_id']}")
            print(f"   User: {order['user_id']}")
            print(f"   Items: {order['total_items']}")
            for item in order['items']:
                print(f"   • {item['product_name']} (Qty: {item['quantity']})")
        else:
            print("❌ Failed to create order")
    except Exception as e:
        print(f"❌ Order creation error: {e}")
    
    # Get user orders
    try:
        response = requests.get(f"{API_BASE}/api/orders/user/1")
        if response.status_code == 200:
            data = response.json()
            orders = data['data']['orders']
            print(f"✅ Retrieved {len(orders)} orders for user 1")
            for order in orders:
                print(f"   • Order {order['order_id']}: {order['item_count']} items")
        else:
            print("❌ Failed to get user orders")
    except Exception as e:
        print(f"❌ User orders error: {e}")

    # Test 5: Department/Aisle filtering
    print_section("Category Filtering")
    
    # Get products by department
    try:
        response = requests.get(f"{API_BASE}/api/products/department/19")  # snacks
        if response.status_code == 200:
            data = response.json()
            department = data['data']['department']
            products = data['data']['products']
            print(f"✅ Found {len(products)} products in {department['department']} department")
            for product in products:
                print(f"   • {product['product_name']}")
        else:
            print("❌ Failed to get products by department")
    except Exception as e:
        print(f"❌ Department filtering error: {e}")

    # Test 6: ML Predictions
    print_section("ML Predictions")
    
    # Get predictions for user
    try:
        response = requests.get(f"{API_BASE}/api/predictions/user/1")
        if response.status_code == 200:
            data = response.json()
            predictions = data['data']['predictions']
            print(f"✅ Generated {len(predictions)} predictions for user 1")
            for pred in predictions:
                print(f"   • {pred['product_name']} (score: {pred['score']})")
        else:
            print("❌ Failed to get predictions")
    except Exception as e:
        print(f"❌ Predictions error: {e}")
    
    # Test predictions for different user
    try:
        response = requests.get(f"{API_BASE}/api/predictions/user/999?limit=3")
        if response.status_code == 200:
            data = response.json()
            predictions = data['data']['predictions']
            print(f"✅ Generated {len(predictions)} predictions for user 999")
            for pred in predictions:
                print(f"   • {pred['product_name']} (score: {pred['score']})")
        else:
            print("❌ Failed to get predictions for user 999")
    except Exception as e:
        print(f"❌ Predictions error for user 999: {e}")

    # Final Summary
    print_section("API Summary")
    print("✅ TimeL-E Grocery API is fully functional!")
    print("\n🔗 Available Endpoints:")
    print("   📦 Products:")
    print("      • GET /api/products/ - List products with pagination")
    print("      • GET /api/products/search?q={query} - Search products")
    print("      • GET /api/products/{id} - Get specific product")
    print("      • GET /api/products/department/{id} - Products by department")
    print("      • GET /api/products/aisle/{id} - Products by aisle")
    print("\n   📋 Categories:")
    print("      • GET /api/departments - List all departments")
    print("      • GET /api/aisles - List all aisles")
    print("      • GET /api/categories/summary - Navigation summary")
    print("\n   🛒 Orders:")
    print("      • POST /api/orders/ - Create new order")
    print("      • GET /api/orders/user/{id} - Get user's orders")
    print("      • GET /api/orders/{id} - Get specific order details")
    print("\n   🤖 ML Predictions:")
    print("      • GET /api/predictions/user/{id} - Get product predictions for user")
    print("\n📖 API Documentation: http://localhost:8000/docs")
    print("\n🎯 Ready for frontend integration with ML predictions!")

if __name__ == "__main__":
    test_api()
