# TimeL-E Grocery Backend API

A domain-specific backend API for the TimeL-E grocery e-commerce application, built around real CSV data structures and designed for frontend integration.

## Architecture

This backend serves as a **Grocery-Focused API** that:
- ✅ Serves real grocery data based on CSV file structure
- ✅ Provides domain-specific endpoints (products, orders, categories)
- ✅ Includes smart product search and filtering
- ✅ Handles order management with product validation
- ✅ Offers category navigation (departments & aisles)
- ✅ Returns frontend-ready responses with joined data

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── base.py          # Base response formats
│   │   └── grocery.py       # CSV-based grocery models
│   ├── routers/             # API route modules
│   │   ├── __init__.py
│   │   ├── products.py      # Product operations & search
│   │   ├── orders.py        # Order management
│   │   └── categories.py    # Department/aisle navigation
│   └── services/            # Data services
│       ├── __init__.py
│       ├── mock_data.py     # CSV data loader & mock responses
│       ├── base_client.py   # HTTP client base (for future use)
│       ├── database_service.py  # Database service (for future use)
│       ├── ml_service.py    # ML service (for future use)
│       └── http_client.py   # Service imports
├── Dockerfile               # Container configuration
└── requirements.txt         # Python dependencies
```

## Data Model (Based on CSV Files)

### **Products** (`products.csv`)
```json
{
  "product_id": 1,
  "product_name": "Chocolate Sandwich Cookies",
  "aisle_id": 61,
  "department_id": 19,
  "aisle_name": "cookies cakes",      // joined data
  "department_name": "snacks"         // joined data
}
```

### **Orders** (`orders.csv`)
```json
{
  "order_id": 2539329,
  "user_id": 1,
  "eval_set": "prior",
  "order_number": 1,
  "order_dow": 2,                     // day of week
  "order_hour_of_day": 8,
  "days_since_prior_order": null
}
```

### **Order Items** (`order_products__prior.csv`)
```json
{
  "order_id": 1,
  "product_id": 49302,
  "add_to_cart_order": 1,             // sequence in cart
  "reordered": 1,                     // 0 or 1
  "product_name": "Bulgarian Yogurt"  // joined data
}
```

### **Categories**
```json
// Departments (departments.csv)
{"department_id": 1, "department": "frozen"}

// Aisles (aisles.csv)  
{"aisle_id": 1, "aisle": "prepared soups salads"}
```

## API Endpoints

### **Product Operations**
- `GET /api/products/` - List products with pagination
- `GET /api/products/search?q={query}` - Search products by name
- `GET /api/products/{product_id}` - Get specific product details
- `GET /api/products/department/{department_id}` - Products in department
- `GET /api/products/aisle/{aisle_id}` - Products in aisle

### **Category Navigation**
- `GET /api/departments` - List all departments
- `GET /api/departments/{department_id}` - Specific department info
- `GET /api/aisles` - List all aisles
- `GET /api/aisles/{aisle_id}` - Specific aisle info
- `GET /api/departments/{department_id}/aisles` - Aisles in department
- `GET /api/categories/summary` - Complete navigation structure

### **Order Management**
- `POST /api/orders/` - Create new order
- `GET /api/orders/user/{user_id}` - Get user's orders
- `GET /api/orders/{order_id}` - Get order with items
- `GET /api/orders/{order_id}/items` - Get order items only
- `POST /api/orders/{order_id}/items` - Add items to order

### **ML Predictions**
- `GET /api/predictions/user/{user_id}` - Get product recommendations for user

### **System Endpoints**
- `GET /health` - API health check
- `GET /` - API information
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Quick Start

### Using Docker (Recommended)

1. **Start the API:**
   ```bash
   docker-compose up --build
   ```

2. **Access the API:**
   - API Gateway: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Local Development

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload
   ```

## Configuration

The backend uses these environment variables:

- `DB_SERVICE_URL` - Future database service URL
- `ML_SERVICE_URL` - Future ML service URL  
- `DEBUG` - Enable debug mode (default: true)
- `SERVICE_TIMEOUT` - Request timeout in seconds (default: 30)

## Example Usage

### **Search for Products**
```bash
curl "http://localhost:8000/api/products/search?q=chocolate"
```
```json
{
  "success": true,
  "message": "Found 1 products matching 'chocolate'",
  "data": {
    "products": [
      {
        "product_id": 1,
        "product_name": "Chocolate Sandwich Cookies",
        "aisle_name": "cookies cakes",
        "department_name": "snacks"
      }
    ]
  }
}
```

### **Get Products by Department**
```bash
curl "http://localhost:8000/api/products/department/19"
```

### **Create Order**
```bash
curl -X POST "http://localhost:8000/api/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ]
  }'
```

### **Get Category Navigation**
```bash
curl "http://localhost:8000/api/categories/summary"
```

### **Get ML Predictions**
```bash
curl "http://localhost:8000/api/predictions/user/1"
```
```json
{
  "success": true,
  "message": "Generated 2 predictions for user 1",
  "data": {
    "user_id": 1,
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
    "total": 2
  }
}
```

## Mock Data Service

The API currently uses a mock data service that:

- **Loads CSV structure** from your data files (with fallback data)
- **Provides realistic responses** matching your actual data format
- **Includes joined data** (product names with department/aisle info)
- **Handles relationships** between products, departments, and aisles
- **Supports all operations** (search, filtering, pagination)

**CSV Files Used:**
- `data/products.csv` - Product catalog
- `data/departments.csv` - Department categories  
- `data/aisles.csv` - Aisle categories
- `data/orders.csv` - Order history
- `data/order_products__prior.csv` - Order items

## Frontend Integration

### **Response Format**
All endpoints return consistent responses:
```json
{
  "success": true,
  "message": "Operation description",
  "data": { /* endpoint-specific data */ },
  "timestamp": "2025-07-04T13:40:08.370054"
}
```

### **Pagination Support**
```json
{
  "products": [...],
  "total": 1000,
  "page": 1,
  "per_page": 50,
  "has_next": true,
  "has_prev": false
}
```

### **Error Handling**
```json
{
  "detail": "Product 999 not found"
}
```

## Testing

### **Run Comprehensive Tests**
```bash
python3 test_new_api.py
```

### **Manual Testing**
- **Health**: `curl http://localhost:8000/health`
- **Products**: `curl http://localhost:8000/api/products/`
- **Search**: `curl "http://localhost:8000/api/products/search?q=cookie"`
- **Departments**: `curl http://localhost:8000/api/departments`

## Development Workflow

### **Current State: Mock Data**
The API currently serves mock data based on your CSV structure. Perfect for:
- ✅ Frontend development
- ✅ API contract validation  
- ✅ UI/UX testing
- ✅ Performance testing

### **Next Steps: Database Integration**
To connect real database:
1. Replace `mock_data.py` with database calls
2. Update service URLs in configuration
3. Keep the same API contracts

### **Future Enhancements**
- Connect real database service
- Add ML recommendations
- Implement user authentication
- Add inventory management
- Include pricing information

## Health Monitoring

- **API Health**: `GET /health`
- **System Info**: `GET /`
- **Documentation**: `GET /docs`

## Architecture Benefits

- **Domain-Focused**: Built specifically for grocery e-commerce
- **Data-Driven**: Based on your actual CSV data structure
- **Frontend-Ready**: Responses optimized for UI consumption
- **Scalable**: Clean separation between data and business logic
- **Testable**: Comprehensive test coverage with mock data
- **Documented**: Auto-generated API documentation
- **Containerized**: Docker-ready for easy deployment

The TimeL-E Grocery API provides a solid foundation for your e-commerce platform with realistic data structures and comprehensive functionality for managing products, orders, and categories.
