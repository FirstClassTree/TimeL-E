"""
Foreign Key Test Helpers

This module provides utilities for testing database operations while respecting
foreign key constraints. It ensures test data integrity by creating parent
records before child records and cleaning up in the correct order.

Key FK Relationships in TimeL-E:
- products.product_enriched -> products.products (product_id)
- products.products -> products.aisles (aisle_id)
- products.products -> products.departments (department_id)
- orders.carts -> users.users (user_id)
- orders.orders -> users.users (user_id)
- orders.cart_items -> orders.carts (cart_id)
- orders.cart_items -> products.products (product_id)
- orders.order_items -> orders.orders (order_id)
- orders.order_items -> products.products (product_id)
"""

import time
import psycopg2
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, UTC
from contextlib import contextmanager

import pytest  # Required for assert_fk_constraint_violation
from db_service.app.db_core.models.orders import OrderStatus


class FKTestDataManager:
    """
    Manages test data creation and cleanup while respecting FK constraints.
    Creates parent records before children and cleans up in reverse order.
    """
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.created_records = {
            'users': [],
            'departments': [],
            'aisles': [],
            'products': [],
            'product_enriched': [],
            'carts': [],
            'orders': [],
            'cart_items': [],
            'order_items': []
        }
    
    def get_or_create_department(self, department_name: Optional[str] = None) -> int:
        """Get existing department or create a new one"""
        if department_name is None:
            department_name = f"Test Department {int(time.time())}"
        
        with self.conn.cursor() as cur:
            # Try to get existing department
            cur.execute("SELECT department_id FROM products.departments WHERE department = %s", (department_name,))
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # Create new department with retry logic for sequence conflicts
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cur.execute(
                        "INSERT INTO products.departments (department) VALUES (%s) RETURNING department_id",
                        (department_name,)
                    )
                    department_id = cur.fetchone()[0]
                    self.conn.commit()
                    
                    self.created_records['departments'].append(department_id)
                    return department_id
                    
                except psycopg2.IntegrityError as e:
                    self.conn.rollback()
                    if "duplicate key value violates unique constraint" in str(e) and "departments_pkey" in str(e):
                        # Sequence is out of sync, fix it and retry
                        cur.execute("SELECT setval('products.departments_department_id_seq', (SELECT COALESCE(MAX(department_id), 0) + 1 FROM products.departments))")
                        self.conn.commit()
                        continue
                    else:
                        raise
            
            raise Exception(f"Failed to create department after {max_retries} attempts")
    
    def get_or_create_aisle(self, aisle_name: Optional[str] = None) -> int:
        """Get existing aisle or create a new one"""
        if aisle_name is None:
            aisle_name = f"Test Aisle {int(time.time())}"
        
        with self.conn.cursor() as cur:
            # Try to get existing aisle
            cur.execute("SELECT aisle_id FROM products.aisles WHERE aisle = %s", (aisle_name,))
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # Create new aisle with retry logic for sequence conflicts
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cur.execute(
                        "INSERT INTO products.aisles (aisle) VALUES (%s) RETURNING aisle_id",
                        (aisle_name,)
                    )
                    aisle_id = cur.fetchone()[0]
                    self.conn.commit()
                    
                    self.created_records['aisles'].append(aisle_id)
                    return aisle_id
                    
                except psycopg2.IntegrityError as e:
                    self.conn.rollback()
                    if "duplicate key value violates unique constraint" in str(e) and "aisles_pkey" in str(e):
                        # Sequence is out of sync, fix it and retry
                        cur.execute("SELECT setval('products.aisles_aisle_id_seq', (SELECT COALESCE(MAX(aisle_id), 0) + 1 FROM products.aisles))")
                        self.conn.commit()
                        continue
                    else:
                        raise
            
            raise Exception(f"Failed to create aisle after {max_retries} attempts")
    
    def get_existing_user_id(self) -> Optional[str]:
        """Get an existing user ID from the database as string"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users.users LIMIT 1")
            result = cur.fetchone()
            return str(result[0]) if result else None
    
    def get_existing_product_id(self) -> Optional[int]:
        """Get an existing product ID from the database"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT product_id FROM products.products LIMIT 1")
            result = cur.fetchone()
            return result[0] if result else None
    
    def create_test_user(self, email_suffix: Optional[str] = None) -> str:
        """Create a test user and return user_id as string"""
        if email_suffix is None:
            email_suffix = str(int(time.time()))

        timestamp = str(int(time.time() * 1000))  # Ensure uniqueness
        
        user_data = {
            'first_name': 'Test',
            'last_name': f'User{email_suffix}',
            'email_address': f'test_user_{email_suffix}_{timestamp}@fk-test.com',
            'hashed_password': 'test_hash_' + email_suffix,
            'phone_number': f'555-{timestamp[-4:]}',
            'street_address': f'{email_suffix} Test St',
            'city': 'Test City',
            'postal_code': timestamp[:5],
            'country': 'Test Country',
            'pending_order_notification': False,
            'order_notifications_via_email': False
        }
        
        # Create new user with retry logic for sequence conflicts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users.users (first_name, last_name, email_address, hashed_password, phone_number, 
                                               street_address, city, postal_code, country, pending_order_notification, 
                                               order_notifications_via_email)
                        VALUES (%(first_name)s, %(last_name)s, %(email_address)s, %(hashed_password)s, %(phone_number)s,
                                %(street_address)s, %(city)s, %(postal_code)s, %(country)s, %(pending_order_notification)s,
                                %(order_notifications_via_email)s)
                        RETURNING user_id
                    """, user_data)
                    
                    user_id = cur.fetchone()[0]
                    self.conn.commit()
                    
                    self.created_records['users'].append(user_id)
                    return user_id
                    
            except psycopg2.IntegrityError as e:
                self.conn.rollback()
                if "duplicate key value violates unique constraint" in str(e) and "users_pkey" in str(e):
                    # Sequence is out of sync, fix it and retry
                    with self.conn.cursor() as cur:
                        cur.execute("SELECT setval('users.users_user_id_seq', (SELECT COALESCE(MAX(user_id), 0) + 1 FROM users.users))")
                        self.conn.commit()
                    continue
                else:
                    raise
        
        raise Exception(f"Failed to create user after {max_retries} attempts")

    def create_test_product(self, product_name: Optional[str] = None, department_id: Optional[int] = None,
                            aisle_id: Optional[int] = None) -> int:
        """Create a test product with valid FK references"""
        if product_name is None:
            product_name = f"Test Product {int(time.time())}"

        if department_id is None:
            department_id = self.get_or_create_department()

        if aisle_id is None:
            aisle_id = self.get_or_create_aisle()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.conn.cursor() as cur:
                    cur.execute("""
                                INSERT INTO products.products (product_name, aisle_id, department_id)
                                VALUES (%s, %s, %s) RETURNING product_id
                                """, (product_name, aisle_id, department_id))

                    product_id = cur.fetchone()[0]
                    self.conn.commit()
                    self.created_records['products'].append(product_id)
                    return product_id

            except psycopg2.IntegrityError as e:
                self.conn.rollback()
                if "duplicate key value violates unique constraint" in str(e) and "products_pkey" in str(e):
                    # Sequence out of sync, reset sequence and retry
                    with self.conn.cursor() as cur:
                        cur.execute(
                            "SELECT setval('products.products_product_id_seq', (SELECT COALESCE(MAX(product_id), 0) + 1 FROM products.products))")
                        self.conn.commit()
                    continue
                else:
                    raise

        raise Exception(f"Failed to create product after {max_retries} attempts")

    def create_test_product_enriched(self, product_id: Optional[int] = None, description: Optional[str] = None, 
                                   price: Optional[float] = None, image_url: Optional[str] = None) -> int:
        """Create enriched product data with valid product_id FK"""
        if product_id is None:
            # Get existing product or create one
            product_id = self.get_existing_product_id()
            if product_id is None:
                product_id = self.create_test_product()
        
        if description is None:
            description = f"Test product description {int(time.time())}"
        if price is None:
            price = 9.99
        if image_url is None:
            image_url = f"https://example.com/product_{product_id}.jpg"
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products.product_enriched (product_id, description, price, image_url)
                VALUES (%s, %s, %s, %s)
                RETURNING product_id
            """, (product_id, description, price, image_url))
            
            enriched_product_id = cur.fetchone()[0]
            self.conn.commit()
            
            self.created_records['product_enriched'].append(enriched_product_id)
            return enriched_product_id
    
    def create_test_cart(self, user_id: Optional[str] = None, total_items: int = 0) -> int:
        """Create a test cart with valid user_id FK"""
        if user_id is None:
            # Get existing user or create one
            user_id = self.get_existing_user_id()
            if user_id is None:
                user_id = self.create_test_user()
        
        now = datetime.now(UTC)
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders.carts (user_id, total_items, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                RETURNING cart_id
            """, (user_id, total_items, now, now))
            
            cart_id = cur.fetchone()[0]
            self.conn.commit()
            
            self.created_records['carts'].append(cart_id)
            return cart_id
    
    def create_test_order(self, user_id: Optional[str] = None, order_number: Optional[int] = None,
                         total_items: int = 1, status: str = OrderStatus.PENDING.value,
                         delivery_name: Optional[str] = None, total_price: Optional[float] = None) -> int:
        """Create a test order with valid user_id FK"""
        if user_id is None:
            # Get existing user or create one
            user_id = self.get_existing_user_id()
            if user_id is None:
                user_id = self.create_test_user()

        if order_number is None:
            order_number = int(time.time())
        
        if delivery_name is None:
            delivery_name = f"Test Delivery {int(time.time())}"
        
        if total_price is None:
            total_price = 29.99

        now = datetime.now(UTC)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders.orders (user_id, order_number, order_dow, order_hour_of_day,
                                         total_items, status, delivery_name, total_price, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING order_id
            """, (user_id, order_number, 1, 10, total_items, status, delivery_name, total_price, now, now))
            
            order_id = cur.fetchone()[0]
            self.conn.commit()
            
            self.created_records['orders'].append(order_id)
            return order_id
    
    def create_test_cart_item(self, cart_id: Optional[int] = None, product_id: Optional[int] = None,
                            quantity: int = 1, add_to_cart_order: int = 1, reordered: int = 0) -> Tuple[int, int]:
        """Create a test cart item with valid FK references"""
        if cart_id is None:
            cart_id = self.create_test_cart()
        
        if product_id is None:
            # Get existing product or create one
            product_id = self.get_existing_product_id()
            if product_id is None:
                product_id = self.create_test_product()
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders.cart_items (cart_id, product_id, add_to_cart_order, reordered, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, (cart_id, product_id, add_to_cart_order, reordered, quantity))
            
            self.conn.commit()
            
            self.created_records['cart_items'].append((cart_id, product_id))
            return cart_id, product_id
    
    def create_test_order_item(self, order_id: Optional[int] = None, product_id: Optional[int] = None,
                             quantity: int = 1, add_to_cart_order: int = 1, reordered: int = 0,
                             price: Optional[float] = None) -> Tuple[int, int]:
        """Create a test order item with valid FK references"""
        if order_id is None:
            order_id = self.create_test_order()
        
        if product_id is None:
            # Get existing product or create one
            product_id = self.get_existing_product_id()
            if product_id is None:
                product_id = self.create_test_product()
        
        if price is None:
            price = 12.99
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders.order_items (order_id, product_id, add_to_cart_order, reordered, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, product_id, add_to_cart_order, reordered, quantity, price))
            
            self.conn.commit()
            
            self.created_records['order_items'].append((order_id, product_id))
            return order_id, product_id
    
    def cleanup_all(self):
        """Clean up all created test data in reverse dependency order"""
        try:
            with self.conn.cursor() as cur:
                # Delete in reverse dependency order
                
                # 1. Delete order_items (depends on orders and products)
                for order_id, product_id in self.created_records['order_items']:
                    cur.execute("DELETE FROM orders.order_items WHERE order_id = %s AND product_id = %s", 
                              (order_id, product_id))
                
                # 2. Delete cart_items (depends on carts and products)
                for cart_id, product_id in self.created_records['cart_items']:
                    cur.execute("DELETE FROM orders.cart_items WHERE cart_id = %s AND product_id = %s", 
                              (cart_id, product_id))
                
                # 3. Delete orders (depends on users)
                for order_id in self.created_records['orders']:
                    cur.execute("DELETE FROM orders.orders WHERE order_id = %s", (order_id,))
                
                # 4. Delete carts (depends on users)
                for cart_id in self.created_records['carts']:
                    cur.execute("DELETE FROM orders.carts WHERE cart_id = %s", (cart_id,))
                
                # 5. Delete product_enriched (depends on products)
                for product_id in self.created_records['product_enriched']:
                    cur.execute("DELETE FROM products.product_enriched WHERE product_id = %s", (product_id,))
                
                # 6. Delete products (depends on aisles and departments)
                for product_id in self.created_records['products']:
                    cur.execute("DELETE FROM products.products WHERE product_id = %s", (product_id,))
                
                # 7. Delete aisles (no dependencies)
                for aisle_id in self.created_records['aisles']:
                    cur.execute("DELETE FROM products.aisles WHERE aisle_id = %s", (aisle_id,))
                
                # 8. Delete departments (no dependencies)
                for department_id in self.created_records['departments']:
                    cur.execute("DELETE FROM products.departments WHERE department_id = %s", (department_id,))
                
                # 9. Delete users (no dependencies)
                for user_id in self.created_records['users']:
                    cur.execute("DELETE FROM users.users WHERE user_id = %s", (user_id,))
                
                self.conn.commit()
                
        except Exception as e:
            self.conn.rollback()
            print(f"Warning: Cleanup failed: {e}")
        finally:
            # Clear tracking
            for key in self.created_records:
                self.created_records[key].clear()


@contextmanager
def fk_test_context(db_connection):
    """
    Context manager for FK-safe testing.
    Automatically cleans up all created test data on exit.
    
    Usage:
        with fk_test_context(db_connection) as fk_manager:
            product_id = fk_manager.create_test_product()
            enriched_id = fk_manager.create_test_product_enriched(product_id)
            # Test operations...
        # Automatic cleanup happens here
    """
    manager = FKTestDataManager(db_connection)
    try:
        yield manager
    finally:
        manager.cleanup_all()


def get_valid_foreign_keys(db_connection) -> Dict[str, List[int]]:
    """
    Get lists of valid foreign key values from the database.
    Useful for tests that need to reference existing data.
    
    Returns:
        Dictionary with lists of valid IDs for each FK relationship
    """
    valid_keys = {
        'user_ids': [],
        'product_ids': [],
        'department_ids': [],
        'aisle_ids': [],
        'cart_ids': [],
        'order_ids': []
    }
    
    with db_connection.cursor() as cur:
        # Get valid user IDs
        cur.execute("SELECT user_id FROM users.users LIMIT 10")
        valid_keys['user_ids'] = [row[0] for row in cur.fetchall()]
        
        # Get valid product IDs
        cur.execute("SELECT product_id FROM products.products LIMIT 10")
        valid_keys['product_ids'] = [row[0] for row in cur.fetchall()]
        
        # Get valid department IDs
        cur.execute("SELECT department_id FROM products.departments LIMIT 10")
        valid_keys['department_ids'] = [row[0] for row in cur.fetchall()]
        
        # Get valid aisle IDs
        cur.execute("SELECT aisle_id FROM products.aisles LIMIT 10")
        valid_keys['aisle_ids'] = [row[0] for row in cur.fetchall()]
        
        # Get valid cart IDs
        cur.execute("SELECT cart_id FROM orders.carts LIMIT 10")
        valid_keys['cart_ids'] = [row[0] for row in cur.fetchall()]
        
        # Get valid order IDs
        cur.execute("SELECT order_id FROM orders.orders LIMIT 10")
        valid_keys['order_ids'] = [row[0] for row in cur.fetchall()]
    
    return valid_keys


def create_test_data_with_fks(db_connection, include_enriched: bool = True, 
                            include_orders: bool = True, include_carts: bool = True) -> Dict[str, Any]:
    """
    Create a complete set of test data with all FK relationships properly established.
    
    Args:
        db_connection: Database connection
        include_enriched: Whether to create product_enriched data
        include_orders: Whether to create orders and order_items
        include_carts: Whether to create carts and cart_items
    
    Returns:
        Dictionary with all created IDs for use in tests
    """
    with fk_test_context(db_connection) as fk_manager:
        # Create base data
        user_id = fk_manager.create_test_user()
        product_id = fk_manager.create_test_product()
        
        result = {
            'user_id': user_id,
            'product_id': product_id
        }
        
        if include_enriched:
            enriched_id = fk_manager.create_test_product_enriched(product_id)
            result['enriched_product_id'] = enriched_id
        
        if include_orders:
            order_id = fk_manager.create_test_order(user_id)
            order_item_ids = fk_manager.create_test_order_item(order_id, product_id)
            result['order_id'] = order_id
            result['order_item_order_id'] = order_item_ids[0]
            result['order_item_product_id'] = order_item_ids[1]
        
        if include_carts:
            cart_id = fk_manager.create_test_cart(user_id)
            cart_item_ids = fk_manager.create_test_cart_item(cart_id, product_id)
            result['cart_id'] = cart_id
            result['cart_item_cart_id'] = cart_item_ids[0]
            result['cart_item_product_id'] = cart_item_ids[1]
        
        return result


def assert_fk_constraint_violation(db_connection, table_name: str, insert_data: Dict[str, Any], 
                                 expected_fk_field: str):
    """
    Assert that inserting data with invalid FK raises a constraint violation.
    
    Args:
        db_connection: Database connection
        table_name: Full table name (e.g., 'products.product_enriched')
        insert_data: Data to insert (should contain invalid FK)
        expected_fk_field: The FK field that should cause the violation
    """
    with db_connection.cursor() as cur:
        # Build INSERT statement
        fields = list(insert_data.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join(fields)
        
        query = f"INSERT INTO {table_name} ({field_names}) VALUES ({placeholders})"
        
        # Expect FK constraint violation
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            cur.execute(query, list(insert_data.values()))
            db_connection.commit()
        
        # Verify it's the expected FK constraint
        error_message = str(exc_info.value).lower()
        assert 'foreign key constraint' in error_message or 'violates foreign key' in error_message
        assert expected_fk_field.lower() in error_message
        
        # Rollback the failed transaction
        db_connection.rollback()


# Example usage functions for common test patterns

# def create_product_test_data(db_connection) -> Dict[str, int]:
#     """Create test data for product-related testing
#
#     Note: This function creates persistent test data that is NOT automatically cleaned up.
#     The caller is responsible for cleanup using the returned manager or manual deletion.
#     """
#     fk_manager = FKTestDataManager(db_connection)
#
#     # First create a dedicated test department that will be empty initially
#     with db_connection.cursor() as cur:
#         cur.execute("""
#             INSERT INTO products.departments (department)
#             VALUES ('TEST_DEPARTMENT_FK_HELPER')
#             RETURNING department_id
#         """)
#         test_department_id = cur.fetchone()[0]
#         db_connection.commit()
#
#     try:
#         # Create test data - the helper will create its own department/aisle
#         test_data = {}
#         aisle_id = fk_manager.get_or_create_aisle("TEST_AISLE_FK_HELPER")
#         product_id = fk_manager.create_test_product("Test Product", test_department_id, aisle_id)
#         enriched_id = fk_manager.create_test_product_enriched(product_id)
#
#         test_data.update({
#             'department_id': test_department_id,
#             'aisle_id': aisle_id,
#             'product_id': product_id,
#             'enriched_product_id': enriched_id
#         })
#
#         return test_data
#
#     except Exception as e:
#         # Clean up test department if something went wrong
#         with db_connection.cursor() as cur:
#             cur.execute("DELETE FROM products.departments WHERE department_id = %s", (test_department_id,))
#             db_connection.commit()
#         raise
# In fk_helpers.py
import time

def create_product_test_data(db_connection) -> Dict[str, int]:
    """
    Create test data for product-related testing, with unique FK parent rows.
    Returns dict of IDs for department, aisle, product, enriched.
    Caller must clean up in dependency order!
    """
    fk_manager = FKTestDataManager(db_connection)
    unique_suffix = str(int(time.time() * 1e6))  # microsecond timestamp for unique names

    department_name = f"TEST_DEPT_FK_HELPER_{unique_suffix}"
    aisle_name = f"TEST_AISLE_FK_HELPER_{unique_suffix}"
    product_name = f"Test Product {unique_suffix}"

    # 1. Create unique department
    department_id = fk_manager.get_or_create_department(department_name)
    # 2. Create unique aisle
    aisle_id = fk_manager.get_or_create_aisle(aisle_name)
    # 3. Create product using those FKs
    product_id = fk_manager.create_test_product(product_name, department_id, aisle_id)
    # 4. Create product_enriched
    enriched_id = fk_manager.create_test_product_enriched(product_id)

    return {
        'department_id': department_id,
        'aisle_id': aisle_id,
        'product_id': product_id,
        'enriched_product_id': enriched_id
    }



def create_order_test_data(db_connection) -> Dict[str, Any]:
    """Create test data for order-related testing"""
    fk_manager = FKTestDataManager(db_connection)
    user_id = fk_manager.create_test_user()
    product_id = fk_manager.create_test_product()
    order_id = fk_manager.create_test_order(user_id)
    order_item_order_id, order_item_product_id = fk_manager.create_test_order_item(order_id, product_id)
    return {
        'user_id': user_id,
        'product_id': product_id,
        'order_id': order_id,
        'order_item_order_id': order_item_order_id,
        'order_item_product_id': order_item_product_id,
    }


def create_cart_test_data(db_connection) -> Dict[str, Any]:
    """Create test data for cart-related testing"""
    fk_manager = FKTestDataManager(db_connection)
    user_id = fk_manager.create_test_user()
    product_id = fk_manager.create_test_product()
    cart_id = fk_manager.create_test_cart(user_id)
    cart_item_cart_id, cart_item_product_id = fk_manager.create_test_cart_item(cart_id, product_id)
    return {
        'user_id': user_id,
        'product_id': product_id,
        'cart_id': cart_id,
        'cart_item_cart_id': cart_item_cart_id,
        'cart_item_product_id': cart_item_product_id,
    }
