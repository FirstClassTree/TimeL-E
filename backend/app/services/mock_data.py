# backend/app/services/mock_data.py
import csv
import os
from typing import List, Dict, Optional, Any
from ..models.grocery import Product, Department, Aisle, Order, OrderItem, OrderWithItems

class MockDataService:
    """Service to load and serve mock data from CSV files"""
    
    def __init__(self):
        self.products: List[Product] = []
        self.departments: List[Department] = []
        self.aisles: List[Aisle] = []
        self.orders: List[Order] = []
        self.order_items: List[OrderItem] = []
        
        # Lookup dictionaries for performance
        self.department_lookup: Dict[int, str] = {}
        self.aisle_lookup: Dict[int, str] = {}
        self.product_lookup: Dict[int, Product] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load all CSV data into memory"""
        data_dir = "data"
        
        # Load departments
        try:
            with open(f"{data_dir}/departments.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dept = Department(
                        department_id=int(row['department_id']),
                        department=row['department']
                    )
                    self.departments.append(dept)
                    self.department_lookup[dept.department_id] = dept.department
        except Exception as e:
            print(f"Warning: Could not load departments.csv: {e}")
            # Fallback data
            self.departments = [
                Department(department_id=1, department="frozen"),
                Department(department_id=2, department="other"),
                Department(department_id=3, department="bakery"),
                Department(department_id=4, department="produce"),
                Department(department_id=13, department="pantry"),
                Department(department_id=19, department="snacks")
            ]
            self.department_lookup = {d.department_id: d.department for d in self.departments}
        
        # Load aisles
        try:
            with open(f"{data_dir}/aisles.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aisle = Aisle(
                        aisle_id=int(row['aisle_id']),
                        aisle=row['aisle']
                    )
                    self.aisles.append(aisle)
                    self.aisle_lookup[aisle.aisle_id] = aisle.aisle
        except Exception as e:
            print(f"Warning: Could not load aisles.csv: {e}")
            # Fallback data
            self.aisles = [
                Aisle(aisle_id=1, aisle="prepared soups salads"),
                Aisle(aisle_id=61, aisle="cookies cakes"),
                Aisle(aisle_id=104, aisle="spices seasonings")
            ]
            self.aisle_lookup = {a.aisle_id: a.aisle for a in self.aisles}
        
        # Load products
        try:
            with open(f"{data_dir}/products.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product = Product(
                        product_id=int(row['product_id']),
                        product_name=row['product_name'],
                        aisle_id=int(row['aisle_id']),
                        department_id=int(row['department_id']),
                        aisle_name=self.aisle_lookup.get(int(row['aisle_id']), "unknown"),
                        department_name=self.department_lookup.get(int(row['department_id']), "unknown")
                    )
                    self.products.append(product)
                    self.product_lookup[product.product_id] = product
        except Exception as e:
            print(f"Warning: Could not load products.csv: {e}")
            # Fallback data
            self.products = [
                Product(
                    product_id=1,
                    product_name="Chocolate Sandwich Cookies",
                    aisle_id=61,
                    department_id=19,
                    aisle_name="cookies cakes",
                    department_name="snacks"
                ),
                Product(
                    product_id=2,
                    product_name="All-Seasons Salt",
                    aisle_id=104,
                    department_id=13,
                    aisle_name="spices seasonings",
                    department_name="pantry"
                )
            ]
            self.product_lookup = {p.product_id: p for p in self.products}
        
        # Load orders
        try:
            with open(f"{data_dir}/orders.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    order = Order(
                        order_id=int(row['order_id']),
                        user_id=int(row['user_id']),
                        eval_set=row['eval_set'],
                        order_number=int(row['order_number']),
                        order_dow=int(row['order_dow']),
                        order_hour_of_day=int(row['order_hour_of_day']),
                        days_since_prior_order=float(row['days_since_prior_order']) if row['days_since_prior_order'] else None
                    )
                    self.orders.append(order)
        except Exception as e:
            print(f"Warning: Could not load orders.csv: {e}")
            # Fallback data
            self.orders = [
                Order(
                    order_id=2539329,
                    user_id=1,
                    eval_set="prior",
                    order_number=1,
                    order_dow=2,
                    order_hour_of_day=8,
                    days_since_prior_order=None
                )
            ]
        
        # Load order items
        try:
            with open(f"{data_dir}/order_products__prior.csv", 'r') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= 1000:  # Limit to first 1000 for performance
                        break
                    
                    product_id = int(row['product_id'])
                    product = self.product_lookup.get(product_id)
                    
                    order_item = OrderItem(
                        order_id=int(row['order_id']),
                        product_id=product_id,
                        add_to_cart_order=int(row['add_to_cart_order']),
                        reordered=int(row['reordered']),
                        product_name=product.product_name if product else f"Product {product_id}"
                    )
                    self.order_items.append(order_item)
        except Exception as e:
            print(f"Warning: Could not load order_products__prior.csv: {e}")
            # Fallback data
            self.order_items = [
                OrderItem(
                    order_id=1,
                    product_id=1,
                    add_to_cart_order=1,
                    reordered=1,
                    product_name="Chocolate Sandwich Cookies"
                )
            ]
    
    # Product methods
    def get_products(self, limit: int = 50, offset: int = 0) -> List[Product]:
        """Get paginated products"""
        return self.products[offset:offset + limit]
    
    def get_product(self, product_id: int) -> Optional[Product]:
        """Get specific product"""
        return self.product_lookup.get(product_id)
    
    def search_products(self, query: str, limit: int = 50) -> List[Product]:
        """Search products by name"""
        query_lower = query.lower()
        return [p for p in self.products if query_lower in p.product_name.lower()][:limit]
    
    def get_products_by_department(self, department_id: int) -> List[Product]:
        """Get products in specific department"""
        return [p for p in self.products if p.department_id == department_id]
    
    def get_products_by_aisle(self, aisle_id: int) -> List[Product]:
        """Get products in specific aisle"""
        return [p for p in self.products if p.aisle_id == aisle_id]
    
    # Department methods
    def get_departments(self) -> List[Department]:
        """Get all departments"""
        return self.departments
    
    def get_department(self, department_id: int) -> Optional[Department]:
        """Get specific department"""
        return next((d for d in self.departments if d.department_id == department_id), None)
    
    # Aisle methods
    def get_aisles(self) -> List[Aisle]:
        """Get all aisles"""
        return self.aisles
    
    def get_aisle(self, aisle_id: int) -> Optional[Aisle]:
        """Get specific aisle"""
        return next((a for a in self.aisles if a.aisle_id == aisle_id), None)
    
    # Order methods
    def get_user_orders(self, user_id: int) -> List[Order]:
        """Get orders for specific user"""
        return [o for o in self.orders if o.user_id == user_id]
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """Get specific order"""
        return next((o for o in self.orders if o.order_id == order_id), None)
    
    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get items for specific order"""
        return [item for item in self.order_items if item.order_id == order_id]
    
    def get_order_with_items(self, order_id: int) -> Optional[OrderWithItems]:
        """Get order with its items"""
        order = self.get_order(order_id)
        if not order:
            return None
        
        items = self.get_order_items(order_id)
        return OrderWithItems(
            **order.dict(),
            items=items,
            total_items=len(items)
        )
    
    def get_user_predictions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get ML predictions for user (mock implementation)"""
        # In a real implementation, this would call the ML service
        # For now, we'll create mock predictions based on:
        # 1. User's order history (if available)
        # 2. Popular products
        # 3. Products from departments user has purchased from
        
        user_orders = self.get_user_orders(user_id)
        user_purchased_products = set()
        user_departments = set()
        
        # Get user's purchase history
        for order in user_orders:
            items = self.get_order_items(order.order_id)
            for item in items:
                user_purchased_products.add(item.product_id)
                product = self.product_lookup.get(item.product_id)
                if product:
                    user_departments.add(product.department_id)
        
        # Generate predictions based on:
        # 1. Products from departments user shops in
        # 2. Popular products they haven't bought
        # 3. Add some randomness for diversity
        
        import random
        random.seed(user_id)  # Consistent predictions for same user
        
        candidate_products = []
        
        # Add products from user's preferred departments (higher scores)
        for product in self.products:
            if product.department_id in user_departments and product.product_id not in user_purchased_products:
                score = random.uniform(0.7, 0.95)  # High score for preferred departments
                candidate_products.append({
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "score": score
                })
        
        # Add other popular products (lower scores)
        for product in self.products:
            if product.product_id not in user_purchased_products:
                score = random.uniform(0.3, 0.6)  # Lower score for other products
                candidate_products.append({
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "score": score
                })
        
        # Sort by score and return top N
        candidate_products.sort(key=lambda x: x["score"], reverse=True)
        return candidate_products[:limit]

# Global instance
mock_data = MockDataService()
