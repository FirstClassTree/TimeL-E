"""
Foreign Key Constraint Tests

This module demonstrates proper FK-safe testing patterns and validates
that FK constraints are properly enforced in the database.

Examples of:
- Creating test data with valid FK references
- Testing FK constraint violations
- Proper cleanup of related data
"""

import pytest
import psycopg2
from ..utils.fk_helpers import (
    fk_test_context,
    assert_fk_constraint_violation,
    create_product_test_data,
    create_order_test_data,
    create_cart_test_data
)
from db_service.app.db_core.models.orders import OrderStatus


class TestProductFKConstraints:
    """Test FK constraints for product-related tables"""
    
    def test_create_product_enriched_with_valid_fk(self, db_connection):
        """Test creating product_enriched with valid product_id FK"""
        with fk_test_context(db_connection) as fk_manager:
            # Create a product first (parent record)
            product_id = fk_manager.create_test_product("Test Product")
            
            # Create enriched data with valid FK
            enriched_id = fk_manager.create_test_product_enriched(
                product_id=product_id,
                description="Test description",
                price=19.99,
                image_url="https://example.com/test.jpg"
            )
            
            # Verify the enriched record was created
            assert enriched_id == product_id
            
            # Verify data in database
            with db_connection.cursor() as cur:
                cur.execute(
                    "SELECT description, price FROM products.product_enriched WHERE product_id = %s",
                    (product_id,)
                )
                result = cur.fetchone()
                assert result is not None
                assert result[0] == "Test description"
                assert float(result[1]) == 19.99
    
    def test_create_product_enriched_with_invalid_fk(self, db_connection):
        """Test that creating product_enriched with invalid product_id fails"""
        invalid_product_id = 999999  # Non-existent product_id
        
        insert_data = {
            'product_id': invalid_product_id,
            'description': 'Test description',
            'price': 19.99,
            'image_url': 'https://example.com/test.jpg'
        }
        
        # Should raise FK constraint violation
        assert_fk_constraint_violation(
            db_connection,
            'products.product_enriched',
            insert_data,
            'product_id'
        )
    
    def test_create_product_with_invalid_department_fk(self, db_connection):
        """Test that creating product with invalid department_id fails"""
        with fk_test_context(db_connection) as fk_manager:
            # Create valid aisle
            aisle_id = fk_manager.get_or_create_aisle("Test Aisle")
            
            invalid_department_id = 999999  # Non-existent department_id
            
            insert_data = {
                'product_name': 'Test Product',
                'aisle_id': aisle_id,
                'department_id': invalid_department_id
            }
            
            # Should raise FK constraint violation
            assert_fk_constraint_violation(
                db_connection,
                'products.products',
                insert_data,
                'department_id'
            )
    
    def test_create_product_with_invalid_aisle_fk(self, db_connection):
        """Test that creating product with invalid aisle_id fails"""
        with fk_test_context(db_connection) as fk_manager:
            # Create valid department
            department_id = fk_manager.get_or_create_department("Test Department")
            
            invalid_aisle_id = 999999  # Non-existent aisle_id
            
            insert_data = {
                'product_name': 'Test Product',
                'aisle_id': invalid_aisle_id,
                'department_id': department_id
            }
            
            # Should raise FK constraint violation
            assert_fk_constraint_violation(
                db_connection,
                'products.products',
                insert_data,
                'aisle_id'
            )


class TestOrderFKConstraints:
    """Test FK constraints for order-related tables"""
    
    def test_create_order_with_valid_user_fk(self, db_connection):
        """Test creating order with valid user_id FK"""
        with fk_test_context(db_connection) as fk_manager:
            # Create user first (parent record)
            user_id = fk_manager.create_test_user("order_test")
            
            # Create order with valid FK
            order_id = fk_manager.create_test_order(
                user_id=user_id,
                total_items=3,
                status=OrderStatus.PENDING.value
            )
            
            # Verify order was created
            with db_connection.cursor() as cur:
                cur.execute(
                    "SELECT user_id, total_items, status FROM orders.orders WHERE order_id = %s",
                    (order_id,)
                )
                result = cur.fetchone()
                assert result is not None
                assert result[0] == user_id
                assert result[1] == 3
                assert result[2] == OrderStatus.PENDING.value
    
    def test_create_order_with_invalid_user_fk(self, db_connection):
        """Test that creating order with invalid user_id fails"""
        invalid_user_id = 999999  # Non-existent user_id
        
        insert_data = {
            'user_id': invalid_user_id,
            'order_number': 12345,
            'order_dow': 1,
            'order_hour_of_day': 10,
            'total_items': 1,
            'status': OrderStatus.PENDING.value,
            'created_at': '2024-01-01 10:00:00+00',
            'updated_at': '2024-01-01 10:00:00+00'
        }
        
        # Should raise FK constraint violation
        assert_fk_constraint_violation(
            db_connection,
            'orders.orders',
            insert_data,
            'user_id'
        )
    
    def test_create_order_item_with_valid_fks(self, db_connection):
        """Test creating order_item with valid order_id and product_id FKs"""
        with fk_test_context(db_connection) as fk_manager:
            # Create parent records
            user_id = fk_manager.create_test_user("order_item_test")
            product_id = fk_manager.create_test_product("Test Product")
            order_id = fk_manager.create_test_order(user_id)
            
            # Create order item with valid FKs
            order_item_ids = fk_manager.create_test_order_item(
                order_id=order_id,
                product_id=product_id,
                quantity=2
            )
            
            # Verify order item was created
            with db_connection.cursor() as cur:
                cur.execute(
                    "SELECT quantity FROM orders.order_items WHERE order_id = %s AND product_id = %s",
                    (order_id, product_id)
                )
                result = cur.fetchone()
                assert result is not None
                assert result[0] == 2
    
    def test_create_order_item_with_invalid_order_fk(self, db_connection):
        """Test that creating order_item with invalid order_id fails"""
        with fk_test_context(db_connection) as fk_manager:
            # Create valid product
            product_id = fk_manager.create_test_product("Test Product")
            
            invalid_order_id = 999999  # Non-existent order_id
            
            insert_data = {
                'order_id': invalid_order_id,
                'product_id': product_id,
                'add_to_cart_order': 1,
                'reordered': 0,
                'quantity': 1
            }
            
            # Should raise FK constraint violation
            assert_fk_constraint_violation(
                db_connection,
                'orders.order_items',
                insert_data,
                'order_id'
            )
    
    def test_create_order_item_with_invalid_product_fk(self, db_connection):
        """Test that creating order_item with invalid product_id fails"""
        with fk_test_context(db_connection) as fk_manager:
            # Create valid order
            user_id = fk_manager.create_test_user("order_item_test")
            order_id = fk_manager.create_test_order(user_id)
            
            invalid_product_id = 999999  # Non-existent product_id
            
            insert_data = {
                'order_id': order_id,
                'product_id': invalid_product_id,
                'add_to_cart_order': 1,
                'reordered': 0,
                'quantity': 1
            }
            
            # Should raise FK constraint violation
            assert_fk_constraint_violation(
                db_connection,
                'orders.order_items',
                insert_data,
                'product_id'
            )


class TestCartFKConstraints:
    """Test FK constraints for cart-related tables"""
    
    def test_create_cart_with_valid_user_fk(self, db_connection):
        """Test creating cart with valid user_id FK"""
        with fk_test_context(db_connection) as fk_manager:
            # Create user first (parent record)
            user_id = fk_manager.create_test_user("cart_test")
            
            # Create cart with valid FK
            cart_id = fk_manager.create_test_cart(
                user_id=user_id,
                total_items=0
            )
            
            # Verify cart was created
            with db_connection.cursor() as cur:
                cur.execute(
                    "SELECT user_id, total_items FROM orders.carts WHERE cart_id = %s",
                    (cart_id,)
                )
                result = cur.fetchone()
                assert result is not None
                assert result[0] == user_id
                assert result[1] == 0
    
    def test_create_cart_with_invalid_user_fk(self, db_connection):
        """Test that creating cart with invalid user_id fails"""
        invalid_user_id = 999999  # Non-existent user_id
        
        insert_data = {
            'user_id': invalid_user_id,
            'total_items': 0,
            'created_at': '2024-01-01 10:00:00+00',
            'updated_at': '2024-01-01 10:00:00+00'
        }
        
        # Should raise FK constraint violation
        assert_fk_constraint_violation(
            db_connection,
            'orders.carts',
            insert_data,
            'user_id'
        )
    
    def test_create_cart_item_with_valid_fks(self, db_connection):
        """Test creating cart_item with valid cart_id and product_id FKs"""
        with fk_test_context(db_connection) as fk_manager:
            # Create parent records
            user_id = fk_manager.create_test_user("cart_item_test")
            product_id = fk_manager.create_test_product("Test Product")
            cart_id = fk_manager.create_test_cart(user_id)
            
            # Create cart item with valid FKs
            cart_item_ids = fk_manager.create_test_cart_item(
                cart_id=cart_id,
                product_id=product_id,
                quantity=3
            )
            
            # Verify cart item was created
            with db_connection.cursor() as cur:
                cur.execute(
                    "SELECT quantity FROM orders.cart_items WHERE cart_id = %s AND product_id = %s",
                    (cart_id, product_id)
                )
                result = cur.fetchone()
                assert result is not None
                assert result[0] == 3


class TestFKHelperFunctions:
    """Test the FK helper functions work correctly"""
    
    # def test_create_product_test_data(self, db_connection):
    #     """Test the create_product_test_data helper function"""
    #     test_data = {}  # Initialize to avoid unbound variable warnings
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
    #         test_data = create_product_test_data(db_connection)
    #
    #         # Verify all expected keys are present
    #         expected_keys = ['department_id', 'aisle_id', 'product_id', 'enriched_product_id']
    #         for key in expected_keys:
    #             assert key in test_data
    #             assert isinstance(test_data[key], int)
    #             assert test_data[key] > 0
    #
    #         # Verify relationships in database
    #         with db_connection.cursor() as cur:
    #             # Check product exists and references our test department
    #             cur.execute("""
    #                 SELECT department_id, aisle_id
    #                 FROM products.products
    #                 WHERE product_id = %s
    #             """, (test_data['product_id'],))
    #             result = cur.fetchone()
    #             assert result is not None
    #             assert result[0] == test_department_id  # Verify using our test department
    #             assert result[1] == test_data['aisle_id']
    #
    #             # Check enriched data exists
    #             cur.execute("""
    #                 SELECT product_id
    #                 FROM products.product_enriched
    #                 WHERE product_id = %s
    #             """, (test_data['enriched_product_id'],))
    #             result = cur.fetchone()
    #             assert result is not None
    #             assert result[0] == test_data['product_id']
    #
    #     finally:
    #         # Clean up test data in proper order
    #         with db_connection.cursor() as cur:
    #             # First delete any product_enriched data
    #             if 'enriched_product_id' in test_data:
    #                 cur.execute("DELETE FROM products.product_enriched WHERE product_id = %s",
    #                           (test_data['enriched_product_id'],))
    #
    #             # Then delete products
    #             if 'product_id' in test_data:
    #                 cur.execute("DELETE FROM products.products WHERE product_id = %s",
    #                           (test_data['product_id'],))
    #
    #             # Then delete aisles (if created) - first verify no products reference it
    #             if 'aisle_id' in test_data:
    #                 cur.execute("""
    #                     SELECT COUNT(*)
    #                     FROM products.products
    #                     WHERE aisle_id = %s
    #                 """, (test_data['aisle_id'],))
    #                 product_count = cur.fetchone()[0]
    #                 assert product_count == 0, "Aisle still has products referencing it"
    #                 cur.execute("DELETE FROM products.aisles WHERE aisle_id = %s",
    #                           (test_data['aisle_id'],))
    #
    #             # Finally delete our test department after verifying it's empty
    #             cur.execute("""
    #                 SELECT COUNT(*)
    #                 FROM products.products
    #                 WHERE department_id = %s
    #             """, (test_department_id,))
    #             product_count = cur.fetchone()[0]
    #             assert product_count == 0, "Test department should be empty before deletion"
    #
    #             cur.execute("DELETE FROM products.departments WHERE department_id = %s",
    #                       (test_department_id,))
    #
    #             db_connection.commit()
    def test_create_product_test_data(self, db_connection):
        """Test the create_product_test_data helper function with unique FKs each run."""
        test_data = create_product_test_data(db_connection)
        try:
            # Confirm IDs are present and valid
            expected_keys = ['department_id', 'aisle_id', 'product_id', 'enriched_product_id']
            for key in expected_keys:
                assert key in test_data
                assert isinstance(test_data[key], int)
                assert test_data[key] > 0

            # Confirm relationships in DB
            with db_connection.cursor() as cur:
                # Check product FK
                cur.execute("""
                            SELECT department_id, aisle_id
                            FROM products.products
                            WHERE product_id = %s
                            """, (test_data['product_id'],))
                row = cur.fetchone()
                assert row is not None
                assert row[0] == test_data['department_id']
                assert row[1] == test_data['aisle_id']

                # Check enriched FK
                cur.execute("""
                            SELECT product_id
                            FROM products.product_enriched
                            WHERE product_id = %s
                            """, (test_data['enriched_product_id'],))
                row = cur.fetchone()
                assert row is not None
                assert row[0] == test_data['product_id']

        finally:
            # Clean up in dependency order: enriched → product → aisle → department
            with db_connection.cursor() as cur:
                # Enriched
                cur.execute(
                    "DELETE FROM products.product_enriched WHERE product_id = %s",
                    (test_data['enriched_product_id'],)
                )
                # Product
                cur.execute(
                    "DELETE FROM products.products WHERE product_id = %s",
                    (test_data['product_id'],)
                )
                # Aisle (make sure no products reference it)
                cur.execute("""
                            SELECT COUNT(*)
                            FROM products.products
                            WHERE aisle_id = %s
                            """, (test_data['aisle_id'],))
                assert cur.fetchone()[0] == 0
                cur.execute(
                    "DELETE FROM products.aisles WHERE aisle_id = %s",
                    (test_data['aisle_id'],)
                )
                # Department (make sure no products reference it)
                cur.execute("""
                            SELECT COUNT(*)
                            FROM products.products
                            WHERE department_id = %s
                            """, (test_data['department_id'],))
                assert cur.fetchone()[0] == 0
                cur.execute(
                    "DELETE FROM products.departments WHERE department_id = %s",
                    (test_data['department_id'],)
                )
                db_connection.commit()
    
    def test_create_order_test_data(self, db_connection):
        """Test the create_order_test_data helper function"""
        test_data = create_order_test_data(db_connection)
        
        try:
            # Verify all expected keys are present
            expected_keys = ['user_id', 'product_id', 'order_id', 'order_item_order_id', 'order_item_product_id']
            for key in expected_keys:
                assert key in test_data
                assert isinstance(test_data[key], int)
                assert test_data[key] > 0
            
            # Verify relationships in database
            with db_connection.cursor() as cur:
                # Check order exists and references correct user
                cur.execute("""
                    SELECT user_id 
                    FROM orders.orders 
                    WHERE order_id = %s
                """, (test_data['order_id'],))
                result = cur.fetchone()
                assert result is not None
                assert result[0] == test_data['user_id']
                
                # Check order item exists
                cur.execute("""
                    SELECT order_id, product_id 
                    FROM orders.order_items 
                    WHERE order_id = %s AND product_id = %s
                """, (test_data['order_item_order_id'], test_data['order_item_product_id']))
                result = cur.fetchone()
                assert result is not None
                assert result[0] == test_data['order_id']
                assert result[1] == test_data['product_id']
        
        finally:
            # Clean up test data manually
            with db_connection.cursor() as cur:
                # Delete in reverse dependency order
                cur.execute("DELETE FROM orders.order_items WHERE order_id = %s AND product_id = %s", 
                          (test_data['order_item_order_id'], test_data['order_item_product_id']))
                cur.execute("DELETE FROM orders.orders WHERE order_id = %s", (test_data['order_id'],))
                cur.execute("DELETE FROM products.products WHERE product_id = %s", (test_data['product_id'],))
                cur.execute("DELETE FROM users.users WHERE user_id = %s", (test_data['user_id'],))
                db_connection.commit()
    
    def test_create_cart_test_data(self, db_connection):
        """Test the create_cart_test_data helper function"""
        test_data = create_cart_test_data(db_connection)
        
        try:
            # Verify all expected keys are present
            expected_keys = ['user_id', 'product_id', 'cart_id', 'cart_item_cart_id', 'cart_item_product_id']
            for key in expected_keys:
                assert key in test_data
                assert isinstance(test_data[key], int)
                assert test_data[key] > 0
            
            # Verify relationships in database
            with db_connection.cursor() as cur:
                # Check cart exists and references correct user
                cur.execute("""
                    SELECT user_id 
                    FROM orders.carts 
                    WHERE cart_id = %s
                """, (test_data['cart_id'],))
                result = cur.fetchone()
                assert result is not None
                assert result[0] == test_data['user_id']
                
                # Check cart item exists
                cur.execute("""
                    SELECT cart_id, product_id 
                    FROM orders.cart_items 
                    WHERE cart_id = %s AND product_id = %s
                """, (test_data['cart_item_cart_id'], test_data['cart_item_product_id']))
                result = cur.fetchone()
                assert result is not None
                assert result[0] == test_data['cart_id']
                assert result[1] == test_data['product_id']
        
        finally:
            # Clean up test data manually
            with db_connection.cursor() as cur:
                # Delete in reverse dependency order
                cur.execute("DELETE FROM orders.cart_items WHERE cart_id = %s AND product_id = %s", 
                          (test_data['cart_item_cart_id'], test_data['cart_item_product_id']))
                cur.execute("DELETE FROM orders.carts WHERE cart_id = %s", (test_data['cart_id'],))
                cur.execute("DELETE FROM products.products WHERE product_id = %s", (test_data['product_id'],))
                cur.execute("DELETE FROM users.users WHERE user_id = %s", (test_data['user_id'],))
                db_connection.commit()


class TestDataCleanup:
    """Test that FK-aware cleanup works correctly"""
    
    def test_cleanup_order_preserves_fk_integrity(self, db_connection):
        """Test that cleanup happens in correct order to avoid FK violations"""
        # Create complex test data with multiple FK relationships
        with fk_test_context(db_connection) as fk_manager:
            # Create base data
            user_id = fk_manager.create_test_user("cleanup_test")
            product_id = fk_manager.create_test_product("Cleanup Product")
            
            # Create dependent data
            order_id = fk_manager.create_test_order(user_id)
            cart_id = fk_manager.create_test_cart(user_id)
            
            # Create items that depend on multiple parents
            fk_manager.create_test_order_item(order_id, product_id)
            fk_manager.create_test_cart_item(cart_id, product_id)
            fk_manager.create_test_product_enriched(product_id)
            
            # Verify all data exists
            with db_connection.cursor() as cur:
                # Check all records exist
                cur.execute("SELECT COUNT(*) FROM users.users WHERE user_id = %s", (user_id,))
                assert cur.fetchone()[0] == 1
                
                cur.execute("SELECT COUNT(*) FROM products.products WHERE product_id = %s", (product_id,))
                assert cur.fetchone()[0] == 1
                
                cur.execute("SELECT COUNT(*) FROM orders.orders WHERE order_id = %s", (order_id,))
                assert cur.fetchone()[0] == 1
                
                cur.execute("SELECT COUNT(*) FROM orders.carts WHERE cart_id = %s", (cart_id,))
                assert cur.fetchone()[0] == 1
        
        # After context exit, all data should be cleaned up
        with db_connection.cursor() as cur:
            # Check all records are gone
            cur.execute("SELECT COUNT(*) FROM users.users WHERE user_id = %s", (user_id,))
            assert cur.fetchone()[0] == 0
            
            cur.execute("SELECT COUNT(*) FROM products.products WHERE product_id = %s", (product_id,))
            assert cur.fetchone()[0] == 0
            
            cur.execute("SELECT COUNT(*) FROM orders.orders WHERE order_id = %s", (order_id,))
            assert cur.fetchone()[0] == 0
            
            cur.execute("SELECT COUNT(*) FROM orders.carts WHERE cart_id = %s", (cart_id,))
            assert cur.fetchone()[0] == 0
