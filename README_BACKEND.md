# TimeL-E Backend API

REST API for the TimeL-E grocery e-commerce platform. This backend serves as an API gateway that handles products, users, orders, shopping carts, and ML-powered recommendations.

## Quick Start

Start all services with Docker:
```bash
docker-compose up --build
```

The API will be available at:
- **API**: http://localhost:8000  
- **Interactive Docs Recommended to see endpoints from here!**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health


### Project Structure
```
backend/
├── app/
│   ├── main.py           # FastAPI app setup
│   ├── config.py         # Configuration
│   ├── models/           # Pydantic models  
│   ├── routers/          # API endpoints
│   │   ├── products.py   # Product operations
│   │   ├── users.py      # User management
│   │   ├── cart.py       # Shopping cart
│   │   ├── orders.py     # Order management
│   │   ├── predictions.py # ML recommendations
│   │   └── categories.py # Product categories
│   └── services/         # External service clients
├── Dockerfile
└── requirements.txt
```
## Architecture

The backend connects to two microservices:
- **db-service** - Handles database operations (PostgreSQL)  
- **ml-service** - Provides product recommendations

```
Frontend → Backend API → db-service → PostgreSQL
                    ↘ ml-service
```

## API Endpoints

### Products
Browse and search the product catalog:

```
GET    /api/products/                      # List products with filtering
GET    /api/products/search               # Search products by name
GET    /api/products/department/{id}      # Products in a department
GET    /api/products/aisle/{id}           # Products in an aisle  
GET    /api/products/{id}                 # Get specific product
```

### User Management
Handle user accounts and authentication:

```
POST   /api/users/register                # Create new account
POST   /api/users/login                   # Login
GET    /api/users/login                   # Demo login
POST   /api/users/logout                  # Logout
GET    /api/users/{user_id}               # Get user profile
PUT    /api/users/{user_id}               # Update profile
DELETE /api/users/{user_id}               # Delete account
PUT    /api/users/{user_id}/password      # Change password
PUT    /api/users/{user_id}/email         # Update email
```

### Notification Settings
Manage shopping reminders:

```
GET    /api/users/{user_id}/notification-settings       # Get settings
PUT    /api/users/{user_id}/notification-settings       # Update settings
GET    /api/users/{user_id}/order-status-notifications  # Get notifications
```

### Shopping Cart
Persistent cart management:

```
GET    /api/cart/{user_id}                              # Get user's cart
PUT    /api/cart/{user_id}                              # Replace entire cart
DELETE /api/cart/{user_id}                              # Delete cart
POST   /api/cart/                                       # Create new cart
POST   /api/cart/{user_id}/items                        # Add item to cart
PUT    /api/cart/{user_id}/items/{product_id}           # Update item quantity
DELETE /api/cart/{user_id}/items/{product_id}           # Remove item
DELETE /api/cart/{user_id}/clear                        # Clear cart
POST   /api/cart/{user_id}/checkout                     # Convert cart to order
```

### Orders
Order creation and management:

```
POST   /api/orders/                       # Create new order
GET    /api/orders/user/{user_id}         # Get user's orders
GET    /api/orders/{order_id}             # Get order details
```

### ML Recommendations
AI-powered product suggestions:

```
GET    /api/predictions/user/{user_id}    # Get personalized recommendations
```

### Categories
Browse product categories:

```
GET    /api/departments/                  # List all departments
GET    /api/departments/{department_id}   # Get specific department
```

### System
Health and information endpoints:

```
GET    /                                  # API information
GET    /health                            # Health check
```

## Authentication Flow

1. **Register**: `POST /api/users/register` with user details
2. **Login**: `POST /api/users/login` with email/password  
3. **Use API**: Include user_id in requests that require it
4. **Logout**: `POST /api/users/logout` when done

## Usage Examples

### Get Products
```bash
# List products with filtering
curl "http://localhost:8000/api/products/?limit=10&offset=0"

# Search for products
curl "http://localhost:8000/api/products/search?q=cookies"

# Get products in department
curl "http://localhost:8000/api/products/department/19"
```

### User Registration
```bash
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe", 
    "emailAddress": "john@example.com",
    "password": "securepassword",
    "phoneNumber": "+1-555-0123"
  }'
```

### Managing Cart
```bash
# Get user's cart
curl "http://localhost:8000/api/cart/user123"

# Add item to cart
curl -X POST "http://localhost:8000/api/cart/user123/items" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Checkout cart
curl -X POST "http://localhost:8000/api/cart/user123/checkout"
```

### Create Order
```bash
curl -X POST "http://localhost:8000/api/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 5, "quantity": 1}
    ]
  }'
```

### Get Recommendations
```bash
curl "http://localhost:8000/api/predictions/user/user123"
```

## Response Format

All endpoints return JSON with a consistent structure:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  }
}
```

Error responses include additional error details:
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_TYPE"
}
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```



### API Documentation
Interactive documentation is available at `/docs` when running the server. This includes:
- Complete endpoint documentation
- Request/response schemas  
- Try-it-out functionality
- Authentication details

### Dependencies
The backend requires these services to be running:
- **db-service**: Database operations (port 7000)
- **PostgreSQL**: Data storage  
- **ml-service**: ML predictions (port 8001)

Use `docker-compose up` to start all services together.

## Configuration

Key environment variables:
- `DB_SERVICE_URL` - Database service endpoint
- `ML_SERVICE_URL` - ML service endpoint  
- `DEBUG` - Enable debug mode
- `NODE_ENV` - Environment (development/production)

The backend automatically configures CORS and other settings based on the environment.
