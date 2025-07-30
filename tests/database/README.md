# Database Integrity Tests

This directory contains tests for database-level integrity, constraints, and schema validation for the TimeL-E system.

## Purpose

These tests validate database behavior that spans across multiple tables and services:
- Foreign key constraint enforcement
- Database schema integrity
- Cross-table relationship validation
- Database-level business rules

## Scope

**What belongs here:**
- FK constraint validation across ALL tables (users, products, orders, carts)
- Database schema integrity tests
- Cross-table relationship testing
- Database-level constraint enforcement

**What does NOT belong here:**
- User-specific API flow testing (belongs in `tests/users/`)
- Service-specific endpoint testing (belongs in respective service test directories)
- Business logic testing (belongs in service-specific test directories)

## Test Structure

```
tests/database/
├── README.md                    # This file
├── conftest.py                  # Database test fixtures
├── requirements.txt             # Database testing dependencies
├── test_fk_constraints.py       # Foreign key constraint validation
└── test_schema_integrity.py     # Database schema validation (future)
```

## Key FK Relationships Tested

### Products Schema
- `products.product_enriched` → `products.products` (product_id)
- `products.products` → `products.aisles` (aisle_id)
- `products.products` → `products.departments` (department_id)

### Orders Schema
- `orders.carts` → `users.users` (user_id)
- `orders.orders` → `users.users` (user_id)
- `orders.cart_items` → `orders.carts` (cart_id)
- `orders.cart_items` → `products.products` (product_id)
- `orders.order_items` → `orders.orders` (order_id)
- `orders.order_items` → `products.products` (product_id)

## Running Tests

### Prerequisites
```bash
# Install dependencies
pip install -r tests/database/requirements.txt

# Ensure services are running
docker-compose up -d
```

### Run Database Tests
```bash
# All database integrity tests
pytest tests/database/ -v

# FK constraint tests only
pytest tests/database/test_fk_constraints.py -v

# With coverage
pytest tests/database/ --cov --cov-report=html
```

## Test Utilities

Database tests use shared utilities from `tests/utils/`:
- `fk_helpers.py` - FK-safe test data creation and cleanup
- Automatic cleanup in correct dependency order
- Helper functions for creating test data with valid FK references

## Example Usage

```python
from tests.utils.fk_helpers import fk_test_context

def test_product_fk_constraint(db_connection):
    with fk_test_context(db_connection) as fk_manager:
        # Create parent records first
        product_id = fk_manager.create_test_product()
        
        # Create child record with valid FK
        enriched_id = fk_manager.create_test_product_enriched(product_id)
        
        # Test operations...
    # Automatic cleanup in correct order
```

## Integration with Other Tests

- **User Tests** (`tests/users/`): Focus on user API flows, may use FK helpers for setup
- **Service Tests**: Focus on service-specific logic, may use FK helpers for setup
- **Database Tests** (this directory): Focus on database integrity across all tables

## Maintenance

When adding new tables or FK relationships:
1. Add FK constraint tests to `test_fk_constraints.py`
2. Update FK helpers in `tests/utils/fk_helpers.py` if needed
3. Update this README with new relationships
4. Ensure cleanup order accounts for new dependencies
