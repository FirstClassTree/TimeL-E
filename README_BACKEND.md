# TimeL-E Grocery Backend API

A comprehensive backend API for the TimeL-E grocery e-commerce application, serving as an API Gateway that communicates with a PostgreSQL database via the db-service microservice.

## Architecture

This backend serves as a **Database-Driven API Gateway** that:
- ✅ Connects to PostgreSQL via db-service microservice
- ✅ Provides comprehensive grocery e-commerce endpoints
- ✅ Includes advanced product filtering and search capabilities
- ✅ Handles complete order lifecycle management
- ✅ Offers user account management and authentication
- ✅ Provides cart persistence to prevent data loss
- ✅ Delivers ML-powered product recommendations
- ✅ Returns frontend-ready responses with proper error handling

**Data Flow:**
```
Frontend → Backend (API Gateway) → DB-Service → PostgreSQL
```

## Quick Start

### Build and run all services:
```bash
docker-compose up --build
```

### Build and run backend only:
```bash
docker-compose up backend --build
```

### Stop services:
```bash
docker-compose down
```

### Access the API:
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health


## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & router setup
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── base.py          # Base response formats
│   │   └── grocery.py       # Database-aligned models with UUIDs
│   ├── routers/             # API route modules
│   │   ├── __init__.py
│   │   ├── products.py      # Enhanced product operations & filtering
│   │   ├── orders.py        # Complete order lifecycle management
│   │   ├── predictions.py   # ML-powered recommendations
│   │   ├── users.py         # User account management
│   │   ├── cart.py          # Cart persistence & management
│   │   └── categories.py    # Department/aisle navigation
│   └── services/            # Data services
│       ├── __init__.py
│       ├── database_service.py  # DB-service communication layer
│       ├── base_client.py   # HTTP client base
│       ├── ml_service.py    # ML service integration
│       ├── http_client.py   # Service imports
│       └── mock_data.py     # Legacy mock data (deprecated)
├── Dockerfile               # Container configuration
└── requirements.txt         # Python dependencies
```

## Data Model (Database Schema Aligned)

### **Products** (`products.products`)
```json
{
  "product_id": 1,
  "product_name": "Chocolate Sandwich Cookies",
  "aisle_id": 61,
  "department_id": 19,
  "aisle_name": "cookies cakes",      // joined from products.aisles
  "department_name": "snacks"         // joined from products.departments
}
```

### **Orders** (`orders.orders`)
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",  // UUID
  "user_id": "550e8400-e29b-41d4-a716-446655440001",   // UUID
  "eval_set": "prior",
  "order_number": 1,
  "order_dow": 2,                     // day of week
  "order_hour_of_day": 8,
  "days_since_prior_order": null,
  "total_items": 3,
  "status": "delivered",              // enum: pending, processing, shipped, delivered, cancelled, etc.
  // Delivery & tracking information
  "phone_number": "+1-555-0123",
  "street_address": "123 Main St",
  "city": "Springfield",
  "postal_code": "12345",
  "country": "USA",
  "tracking_number": "1Z999AA1234567890",
  "shipping_carrier": "UPS",
  "tracking_url": "https://ups.com/track/..."
}
```

### **Order Items** (`orders.order_items`)
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",  // UUID
  "product_id": 49302,
  "add_to_cart_order": 1,             // sequence in cart
  "reordered": 1,                     // 0 or 1
  "quantity": 2,                      // item quantity
  "product_name": "Bulgarian Yogurt"  // joined from products.products
}
```

### **Users** (`users.users`)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",   // UUID
  "name": "john_doe",
  "email_address": "john@example.com",
  "phone_number": "+1-555-0123",
  "street_address": "123 Main St",
  "city": "Springfield",
  "postal_code": "12345",
  "country": "USA"
  // hashed_password field excluded from responses
}
```

### **Categories**
```json
// Departments (products.departments)
{"department_id": 1, "department": "frozen"}

// Aisles (products.aisles)  
{"aisle_id": 1, "aisle": "prepared soups salads"}
```

## API Endpoints

### **Enhanced Product Operations**
- `GET /api/products/` - List products with pagination & filtering
  - Query params: `limit`, `offset`, `categories[]`
- `GET /api/products/search?q={query}` - Search products by name
- `GET /api/products/{product_id}` - Get specific product details
- `GET /api/products/{product_id}/recommendations` - ML recommendations based on product
- `GET /api/products/department/{department_id}` - Products in department
- `GET /api/products/aisle/{aisle_id}` - Products in aisle

### **Complete Order Lifecycle Management**
- `POST /api/orders/` - Create new order with validation
- `GET /api/orders/user/{user_id}` - Get user's orders with filtering & pagination
  - Query params: `limit`, `offset`, `status`, `sort`
- `GET /api/orders/{order_id}` - Get order with all items included
- `GET /api/orders/{order_id}/items` - Get order items only
- `POST /api/orders/{order_id}/items` - Add items to existing order
- `POST /api/orders/{order_id}/cancel` - Cancel order
- `GET /api/orders/{order_id}/tracking` - Get shipment tracking info
- `GET /api/orders/{order_id}/invoice` - Get order invoice (PDF/blob)
- `GET /api/orders/{order_id}/delivery` - Get delivery details
- `GET /api/orders/recommendations` - ML-based product recommendations from order history

### **User Account Management**
- `GET /api/users/{user_id}` - Get user profile
- `POST /api/users/register` - Create new user account
- `PUT /api/users/{user_id}` - Update user profile details
- `DELETE /api/users/{user_id}` - Delete user account
- `POST /api/users/{user_id}/password` - Update user password

### **Cart Persistence & Management**
- `GET /api/cart/{user_id}` - Get user's cart with product details
- `POST /api/cart/{user_id}` - Replace entire cart
- `POST /api/cart/{user_id}/items` - Add items to cart
- `PUT /api/cart/{user_id}/items/{product_id}` - Update item quantity
- `DELETE /api/cart/{user_id}/items/{product_id}` - Remove specific item
- `DELETE /api/cart/{user_id}` - Clear entire cart
- `POST /api/cart/{user_id}/checkout` - Convert cart to order

### **Enhanced ML Predictions**
- `GET /api/predictions/user/{user_id}` - Get ML recommendations with pagination
  - Query params: `limit`, `offset`

### **Category Navigation**
- `GET /api/departments` - List all departments
- `GET /api/departments/{department_id}` - Specific department info
- `GET /api/aisles` - List all aisles
- `GET /api/aisles/{aisle_id}` - Specific aisle info
- `GET /api/departments/{department_id}/aisles` - Aisles in department
- `GET /api/categories/summary` - Complete navigation structure

### **System Endpoints**
- `GET /health` - API health check
- `GET /` - API information
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation


## Configuration

The backend uses these environment variables:

- `DB_SERVICE_URL` - Database service URL (required for all operations)
- `ML_SERVICE_URL` - ML service URL for advanced recommendations
- `DEBUG` - Enable debug mode (default: true)
- `SERVICE_TIMEOUT` - Request timeout in seconds (default: 30)
- `PROJECT_NAME` - API project name
- `VERSION` - API version

**Required Services:**
- **db-service**: Must be running on configured URL for database operations
- **PostgreSQL**: Database backend accessed via db-service

## Example Usage

### **Enhanced Product Search with Filtering**
```bash
curl "http://localhost:8000/api/products/?categories=snacks&categories=frozen&limit=10&offset=0"
```
```json
{
  "success": true,
  "message": "Products retrieved successfully",
  "data": {
    "products": [
      {
        "product_id": 1,
        "product_name": "Chocolate Sandwich Cookies",
        "aisle_name": "cookies cakes",
        "department_name": "snacks"
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

### **Get Product Recommendations**
```bash
curl "http://localhost:8000/api/products/1/recommendations?limit=5"
```

### **Enhanced Order Management**
```bash
# Create order with UUIDs
curl -X POST "http://localhost:8000/api/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ]
  }'

# Get user orders with filtering
curl "http://localhost:8000/api/orders/user/550e8400-e29b-41d4-a716-446655440001?status=delivered&limit=10&sort=desc"

# Cancel order
curl -X POST "http://localhost:8000/api/orders/550e8400-e29b-41d4-a716-446655440000/cancel"

# Get tracking info
curl "http://localhost:8000/api/orders/550e8400-e29b-41d4-a716-446655440000/tracking"
```

### **User Account Management**
```bash
# Register new user
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john_doe",
    "email_address": "john@example.com",
    "password": "secure_password",
    "phone_number": "+1-555-0123",
    "street_address": "123 Main St",
    "city": "Springfield",
    "postal_code": "12345",
    "country": "USA"
  }'

# Get user profile
curl "http://localhost:8000/api/users/550e8400-e29b-41d4-a716-446655440001"

# Update user profile
curl -X PUT "http://localhost:8000/api/users/550e8400-e29b-41d4-a716-446655440001" \
  -H "Content-Type: application/json" \
  -d '{"city": "New Springfield", "phone_number": "+1-555-0124"}'
```

### **Cart Management**
```bash
# Get user cart
curl "http://localhost:8000/api/cart/550e8400-e29b-41d4-a716-446655440001"

# Add item to cart
curl -X POST "http://localhost:8000/api/cart/550e8400-e29b-41d4-a716-446655440001/items" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Update item quantity
curl -X PUT "http://localhost:8000/api/cart/550e8400-e29b-41d4-a716-446655440001/items/1" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3}'

# Checkout cart
curl -X POST "http://localhost:8000/api/cart/550e8400-e29b-41d4-a716-446655440001/checkout"
```

### **Enhanced ML Predictions with Pagination**
```bash
curl "http://localhost:8000/api/predictions/user/550e8400-e29b-41d4-a716-446655440001?limit=10&offset=0"
```
```json
{
  "success": true,
  "message": "Generated 2 predictions for user 550e8400-e29b-41d4-a716-446655440001",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "predictions": [
      {
        "product_id": 2,
        "product_name": "All-Seasons Salt",
        "score": 0.554
      },
      {
        "product_id": 1,
        "product_name": "Chocolate Sandwich Cookies",
        "score": 0.34
      }
    ],
    "total": 2,
    "page": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

## Database Integration

The API connects to a PostgreSQL database via the db-service microservice:

- **Real-time data** from PostgreSQL database
- **Transactional integrity** for order processing  
- **UUID support** for distributed system compatibility
- **Advanced queries** with proper joins and filtering
- **Schema validation** ensuring data consistency
- **Performance optimization** using database indexes

**Database Schema:**
- `products.products` - Product catalog
- `products.departments` - Department categories  
- `products.aisles` - Aisle categories
- `orders.orders` - Order management with full lifecycle
- `orders.order_items` - Order line items with quantities
- `users.users` - User accounts with delivery information

## Testing

### **Manual Testing**
- **Health**: `curl http://localhost:8000/health`
- **Products**: `curl http://localhost:8000/api/products/`
- **Search**: `curl "http://localhost:8000/api/products/search?q=cookie"`
- **Departments**: `curl http://localhost:8000/api/departments`

## Architecture Benefits

- **Database-Driven**: Real PostgreSQL integration via microservice architecture
- **Comprehensive**: Complete e-commerce functionality including user management and cart persistence
- **Scalable**: Clean separation between API gateway and database service
- **Production-Ready**: Proper error handling, validation, and UUID support
- **ML-Powered**: Intelligent product recommendations based on user behavior
- **Frontend-Optimized**: Responses designed for modern web applications
- **Documented**: Auto-generated interactive API documentation
- **Containerized**: Docker-ready for seamless deployment
- **Maintainable**: Clear separation of concerns and modular design

The TimeL-E Grocery API provides a complete, production-ready foundation for e-commerce platforms with advanced features including user management, cart persistence, order tracking, and ML-powered recommendations.
