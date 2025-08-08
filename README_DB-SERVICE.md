# Database Service (db_service)

A comprehensive FastAPI-based database service for the TimeL-E e-commerce platform,  
providing robust data management, user authentication, order processing, and intelligent notifications systems.  
It interfaces with a PostgreSQL database and exposes RESTful endpoints that are consumed by the main backend service.  
The backend sends HTTP requests to this service for database operations (CRUD + query),  
and the db-service translates them to SQLAlchemy operations.    
This allows backend to remain DB-agnostic, and enables swapping/replicating DBs via internal services.

## Quick Start
After all services started with Docker,
```bash
docker-compose up --build
```
The API will be available at:  
- **API**: http://localhost:7000  
- **Interactive API Documentation**: http://localhost:7000/docs (in development mode)  
    a FastAPI web server that automatically generates and serves interactive API documentation for DB Service.
- **Health Check**: http://localhost:7000/health (in development mode)  

**Note**: Ensure the .env file is properly configured with the correct DB credentials.  

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Notification Systems](#notification-systems-1)
- [Data Loading](#data-loading)
- [Development](#development)
- [Production Deployment](#production-deployment)

## Overview

The Database Service is a critical microservice in the TimeL-E platform that handles all database operations,  
user management, order processing, and notification systems.  
Built with FastAPI and SQLAlchemy, it provides a robust, scalable, and secure foundation for the e-commerce platform.

### Key Capabilities

- **User Management**: Complete CRUD operations with secure authentication
- **Notification Systems**: Notification architecture for order scheduling reminders and order status updates
- **Order Processing**: Full order lifecycle management with status tracking
- **Shopping Cart**: Comprehensive cart management with product enrichment
- **Product Catalog**: Rich product data with department/aisle organization
- **Data Integration**: Optimized CSV data loading and validation

### Service Structure

```
db_service/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── init_db.py              # Initializes the PostgreSQL schemas
│   ├── reset_database.py       # Drops all schemas with all tables
│   ├── database_service.py     # Core database endpoints
│   ├── users_routers.py        # User management endpoints
│   ├── carts_routers.py        # Shopping cart endpoints
│   ├── orders_routers.py       # Order management endpoints
│   ├── scheduler.py            # Background notification scheduler
│   ├── notification_service.py # Email notification service
│   ├── db_core/                # Database models and configuration
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── database.py         # SQLAlchemy engine/session setup
│   │   └── config.py           # Configuration settings
│   └── data_loaders/           # CSV data loading utilities
├── requirements.txt            # Python dependencies
└── Dockerfile                  # Container configuration
```

## Architecture

### Microservice Design

The db_service follows a domain-driven microservice architecture with clear separation of concerns:

- **Database Layer**: Centralized data persistence and database operations for the TimeL-E platform
- **API-First Design**: RESTful endpoints with comprehensive OpenAPI documentation
- **Stateless Operations**: Each request is independent, enabling horizontal scaling
- **Event-Driven Notifications**: Background scheduler for asynchronous notification processing

### Data Architecture Patterns

**Schema Separation**:
- **users**: User accounts, authentication, and notification preferences
- **products**: Product catalog, departments, aisles, and enrichment data  
- **orders**: Orders, order items, carts, cart items, and order status history  
Note: review current schema.sql dump and ERD at database/

**Relationship Management**:
- Foreign key constraints ensure referential integrity
- SQLAlchemy relationships enable efficient lazy loading
- Optimized joins for complex queries (cart + product enrichment)

**Data Flow Patterns**:
- **Request → Validation → Database → Response**: Standard CRUD operations
- **Background Scheduler → Database → Email Service**: Notification processing
- **CSV Loader → Batch Processing → Database**: Data integration pipeline
- **Database Triggers → Order Status History**: Automatic audit trail generation

### Transaction Management & Data Consistency

**ACID Compliance**:
- SQLAlchemy session management ensures transactional integrity
- Automatic rollback on constraint violations or errors
- Batch processing with individual error isolation for data loading
- Foreign key constraints maintain referential integrity across schemas

**Concurrency Handling**:
- Session-per-request pattern prevents connection leaks
- Database-level constraints prevent race conditions
- Optimistic concurrency for cart and order operations

### User Dual-ID System

The service implements a dual-ID architecture for User data for optimal performance, API consistency, and security:

- **Internal IDs**: Numeric BIGSERIAL primary keys used internally for database operations and foreign key relationships
- **External IDs**: UUID4 strings exposed to backend (and from there to frontend) via API endpoints
- **Benefits**:  
  - Fast database operations along with secure, non-sequential external identifiers  
  - Unlike auto-increment integers, UUIDv4 values are highly resistant to guessing or enumeration,    
    making the endpoints more secure, even if user IDs are exposed in URLs.  
  - UUID also enables distributed ID generation across multiple servers without collisions.
- **UUID validation** performed for user IDs at each endpoint
- **Migration Strategy**: Deterministic UUID generation from legacy integer IDs (.csv data) for data consistency
- **URL Parameters**: User endpoints use `{user_id}` in URL paths (UUID4 strings)
- **Response Fields**: All API responses return `user_id` serialized as UUID4 strings
- **CSV Loading Logic**:
  - Existing users load with original CSV IDs as internal IDs, UUID external ID is generated deterministically (UUID5).
  - Sequence Configuration: Set starting points for new records
  - New users are assigned sequential internal IDs starting past maximal CSV ID, external UUID is generated as UUID4.

#### Orders & Carts: Simple Integer IDs
- **Single ID System**: Uses integer primary keys starting from preserved ranges
- **Orders**: Integer IDs starting at 3,422,000+ (preserving CSV data integrity)
- **Carts**: Integer IDs starting at 1+
- **URL Parameters**: Order endpoints use `{order_id}` (integer as string)
- **Response Fields**: All API responses return `order_id` and `cart_id` as integer strings

#### User ID Strategy: Legacy Users vs. New Users

##### Legacy Records (migrated from `users_demo.csv`)
- Internal Database Key: Integer (from original legacy data)
- API/Public ID (exposed as `user_id`):
  - Deterministically generated using UUID5 (`uuid.uuid5`)
  - Namespace is fixed for the application (e.g., `USER_UUID_NAMESPACE`)
  - Formula:
    ```python
    external_user_id = uuid.uuid5(USER_UUID_NAMESPACE, str(legacy_integer_id))
    ```

This ensures that the same legacy ID always maps to the same UUID, providing stable references for migration and testing.

##### New Records
- Internal Database Key: Integer (autoincrement starting at 400,000)
- API/Public ID (exposed as `user_id`):
  - Randomly generated using UUID4 (`uuid.uuid4()`)
  - Recommended for all new users created after migration
    ```python
    external_user_id = uuid.uuid4()
    ```
    
#### Fast UUID Lookup with Database Indexing
- To make user lookups efficient via the public API, the `external_user_id` column is both unique and indexed.
- This allows instant retrieval by UUID, essential for APIs that never expose or use the internal numeric PK.


## Features

### User Management
- **Secure Authentication**: Argon2id password hashing
- **Dual-ID Architecture**: Internal numeric IDs for performance + external UUID4 for API security
- **Complete User Lifecycle**: Registration, login, profile retrieval and updates, secure password updates and account deletion
- **Email Management**: Secure email updates with password verification and duplicate prevention
- **Profile Management**: Full contact information, delivery addresses, and personal details
- **Notification Preferences**: Configurable order reminder settings; reminder frequencies (1-365 days), email preferences, and scheduling
- **Session Management**: Login tracking with timezone-aware timestamps
- **Initial Security Features**: Password verification for sensitive operations, input validation, constraint checking
- **Initial Data Privacy**: Sanitized error responses to avoid information leaks

### Order System
- **Order Creation**: Full order processing with validation
- **Order History**: View all orders for a user with pagination and enriched product data
- **Individual Order Details**: Complete order information with full tracking, shipping details, and status update history
- **Status Tracking**: Comprehensive order status update history with timestamps
- **Shipping Integration**: Tracking numbers, carriers, and URLs
- **Invoice Support**: Binary invoice storage and retrieval
- **Enriched Data**: Complete product details with descriptions and images

### Shopping Cart
- **Cart Management**: Create, update, and manage shopping carts
- **Product Enrichment**: Full product details with pricing and images
- **Quantity Management**: Add, update, and remove items
- **Checkout Integration**: Convert cart to order seamlessly

### Notification Systems

#### 1. Scheduled Order Notifications
- **Purpose**: Remind users to reorder based on their preferences
- **Timing**: Configurable intervals (1-365 days) and start date/time for when notifications should begin
- **Delivery**: Email notifications via Resend API (opt-in feature), also sent with user data (e.g on login)
- **Scheduling**: Background scheduler with APScheduler

#### 2. Order Status Notifications
- **Purpose**: Notify users of order status updates (shipped, delivered, etc.)
- **Tracking**: Complete status update history with timestamps
- **Delivery**: Notifications available at the corresponding endpoint (expected to be requested on login)
- **History**: Chronological order status updates tracking
#### 3. Active Cart Notification
- **Purpose**: Included in login response to indicate whether user has active cart

### Data Integrity & Validation
- **Time-Aware Storage**: All datetime fields use PostgreSQL TIMESTAMPTZ with UTC storage for consistent timezone handling
  - Automatic timezone conversion for requests
  - Proper temporal data integrity for notifications and order tracking
- **Pydantic Validation**: Comprehensive input validation and serialization with Pydantic models for all API endpoints
- **Database Constraints**: Foreign key validation, data type constraints, and referential integrity

## API Endpoints

### Core Database Operations

#### Generic Query Interface
- `POST /query` - Execute parameterized SQL queries with validation (intended to be fully deprecated in production)

#### Product Catalog
- `GET /products` - Paginated product listing with filtering and enrichment

### User Management (`/users`)

#### Authentication & Profile
- `POST /users/` - Create new user account
- `POST /users/login` - User authentication
- `GET /users/{user_id}` - Get user profile
- `PUT /users/{user_id}` - Update user profile
- `DELETE /users/{user_id}` - Delete user account (requires password verification)

#### Security
- `PUT /users/{user_id}/password` - Update password with verification
- `PUT /users/{user_id}/email` - Update email with password verification

#### Notification Settings
- `GET /users/{user_id}/notification-settings` - Get notification preferences
- `PUT /users/{user_id}/notification-settings` - Update notification preferences
- `GET /users/{user_id}/order-status-notifications` - Get order status updates

### Order Management (`/orders`)

#### Order Operations
- `POST /orders/` - Create new order
- `GET /orders/user/{user_id}` - Get user's order history (paginated)
- `GET /orders/{order_id}` - Get detailed order information
- `DELETE /orders/{order_id}` - Delete order

#### Order Items
- `POST /orders/{order_id}/items` - Add items to existing order

#### Enhanced Order Details
The detailed order endpoint (`GET /orders/{order_id}`) provides:
- Complete order metadata (delivery address, tracking info)
- Enriched product data (descriptions, images, department/aisle info)
- Full status history (chronological status changes with timestamps)
- Invoice data (binary storage support)
- Tracking integration (carrier, tracking number, tracking URL)

### Shopping Cart (`/carts`)

#### Cart Management
- `GET /carts/{user_id}` - Get user's cart
- `POST /carts/` - Create new cart
- `PUT /carts/{user_id}` - Replace entire cart
- `DELETE /carts/{user_id}` - Delete cart

#### Cart Items
- `POST /carts/{user_id}/items` - Add item to cart
- `PUT /carts/{user_id}/items/{product_id}` - Update item quantity
- `DELETE /carts/{user_id}/items/{product_id}` - Remove item from cart
- `DELETE /carts/{user_id}/clear` - Clear all cart items

#### Cart Operations
- `POST /carts/{user_id}/checkout` - Convert cart to order

### Health & Monitoring
- `GET /` - Service information
- `GET /health` - Health check with database connectivity

## Database Schema

### Users Schema (`users.users`)
```sql
- id (BIGINT, PK) - Internal numeric ID
- external_user_id (UUID, UNIQUE) - External API identifier
- first_name, last_name (VARCHAR) - User name
- email_address (VARCHAR, UNIQUE) - Login email
- hashed_password (VARCHAR) - Argon2id hash
- phone_number, street_address, city, postal_code, country - Contact info
- last_login (TIMESTAMPTZ) - Last login timestamp
- last_notifications_viewed_at (TIMESTAMPTZ) - Order status notifications tracking
- days_between_order_notifications (INT) - Scheduled order notification reminder frequency
- order_notifications_* - Scheduled order notification settings
- pending_order_notification (BOOLEAN) - Scheduled order notification flag
```

### Products Schema
```sql
products.departments - Product categories
products.aisles - Product aisles
products.products - Main product catalog
products.product_enriched - Enhanced product data (descriptions, prices, images)
```

### Orders Schema
```sql
orders.orders - Order records with delivery and tracking info
orders.order_items - Order items with pricing
orders.carts - Shopping carts
orders.cart_items - Cart items
orders.order_status_history - Complete status updates audit trail
```

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL              # PostgreSQL connection string
RESET_DATABASE_ON_STARTUP # Whether to reset database on service startup (false by default)

# Service Configuration
DB_SERVICE_PORT           # Port for the database service to listen on
NODE_ENV                  # Environment mode (development/production)

# Email Notifications
RESEND_API_KEY           # API key for Resend email service
NOTIFICATION_FROM_EMAIL  # Email address for sending notifications
APP_NAME                 # Application name used in notifications

# Application Metadata
VERSION                  # Service version identifier
```

### Configuration Class
Located in `app/db_core/config.py`, provides centralized configuration management with environment variable support and sensible defaults.

## Dependencies

### Core Dependencies
- **FastAPI** (0.116.1) - Modern web framework
- **SQLAlchemy** (2.0.42) - ORM and database toolkit
- **asyncpg** (0.30.0) - Async PostgreSQL driver
- **psycopg2-binary** (2.9.10) - PostgreSQL adapter
- **Pydantic** (2.11.7) - Data validation and serialization

### Security & Authentication
- **argon2-cffi** (25.1.0) - Password hashing
- **email-validator** (2.2.0) - Email validation

### Background Processing
- **APScheduler** (3.11.0) - Task scheduling
- **httpx** (0.28.1) - HTTP client for notifications

### Data Processing
- **pandas** (2.3.1) - Data manipulation
- **numpy** (2.3.2) - Numerical computing

### Server & Deployment
- **uvicorn** (0.35.0) - ASGI server
- **python-dateutil** (2.9.0.post0) - Date/time utilities

## Installation & Setup

### Using Docker

The db_service is designed to run as part of the complete TimeL-E application stack using Docker Compose.

```bash
# Run the complete application stack (from project root)
docker-compose up --build

# The db_service will be available as part of the stack
# Individual service builds are handled by docker-compose.yml
```

## Usage

### Starting the Service

The service automatically:
1. Initializes database schemas and tables (if not present)
2. Loads CSV data if not already present
3. Starts the background notification scheduler
4. Exposes REST API on configured port

### API Documentation

- **Swagger UI**: `http://localhost:7000/docs`
- **ReDoc**: `http://localhost:7000/redoc`

### Health Monitoring

```bash
# Check service health
curl http://localhost:7000/health

# Response includes database connectivity status
{
  "message": "DB service API Gateway is healthy",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-01-08T01:00:00",
    "service": "database-service",
    "database": "reachable"
  }
}
```

## Notification Systems

### Scheduled Order Notifications

**Purpose**: Remind users to reorder based on their shopping patterns.

**Configuration**:
- `days_between_order_notifications`: Interval between reminders (1-365 days)
- `order_notifications_start_date_time`: When to start sending reminders
- `order_notifications_via_email`: Enable/disable email notifications

**Processing**:
- Background scheduler runs hourly to identify users due for notifications
- Sends email via Resend API (if enabled)
- Updates next scheduled time
- Users also receive notification flag with user data (e.g., on login) if notification is pending

### Order Status Notifications

**Purpose**: Notify users of order status updates (shipped, delivered, etc.).

**Features**:
- Status update tracking with database triggers
- Complete chronological history
- Timestamp and attribution tracking
- Efficient querying with user-specific filtering

**Implementation**:
- Database triggers capture status changes
- `OrderStatusHistory` table maintains complete audit trail
- API endpoint provides notifications since last viewed (when requested)
- Automatic timestamp updates for tracking

## Data Loading

### CSV Data Integration

The service includes optimized data loading capabilities:

**Supported Data Types**:
- Users (with authentication and notification settings)
- Products (with department/aisle organization and enriched data)
- Orders (with delivery and tracking information)
- Order Items (with pricing and quantity data)
- Order Status History (complete status updates tracking)

**Features**:
- **Batch Processing**: Efficient bulk data loading
- **Error Handling**: Graceful handling of data inconsistencies
- **Validation**: Foreign key validation and constraint checking
- **Progress Reporting**: Detailed loading progress and statistics

**Data Sources**:
- `/data/users_demo.csv` - User accounts including contact info and timestamps.
- `/data/orders_demo_enriched.csv` - Order data with enrichment
- `/data/orders_demo_status_history.csv` - Status updates history
- `/data/order_items_demo.csv` - Order items
- `/data/products.csv` - Product catalog
- `/data/products_enriched/*` - Enriched product data by department
- `/data/departments.csv` - Departments
- `/data/departments_enriched.csv` - Departments enriched with images and description
- `/data/aisles.csv` - Aisles

**Note**:
- additional products data (description, price, image) is generated by `/data/product_enricher.py` script.
- all other additional data not present in instacart dataset (user information and timestamps, order tracking and statuses)  
  is generated by `/data/make_demo_data.py`.
- all additional data in .csv files was generated ahead of time.

## Development

### Code Structure

**Models** (`app/db_core/models/`):
- `users.py` - User account and notification models
- `orders.py` - Order, cart, and status history models
- `products.py` - Product catalog and enrichment models
- `base.py` - Base model configuration

**Routers**:
- `users_routers.py` - User management endpoints
- `orders_routers.py` - Order processing endpoints
- `carts_routers.py` - Shopping cart endpoints
- `database_service.py` - `/query` and `/products` endpoints

**Services**:
- `scheduler.py` - Background order scheduling notifications processing
- `notification_service.py` - Email notification delivery


### Key Design Patterns

**Dual-ID Architecture for User**:
- Internal numeric IDs for database performance
- External UUID4s for API security and consistency
- Automatic conversion between internal and external representations

**Service Response Pattern**:
```python
class ServiceResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] = []
    error: Optional[str] = None
    message: Optional[str] = None
```

**Error Handling**:
- Comprehensive SQLAlchemy exception handling
- Graceful degradation for data loading errors
- Sanitized generic error responses to prevent sensitive information disclosure
- Detailed error logging with context

### Testing

The service includes comprehensive error handling and validation:
- Foreign key constraint validation
- Data type validation with Pydantic
- Batch processing with individual error isolation
- Transaction rollback on failures


### Testing the API (Example)

Once the `db-service` is running via Docker and port `7000` is mapped,  
one can test if specific endpoints are exposed using curl.

#### Example Request (`POST /users`)

Run from the **host machine**.

##### Linux / macOS / Git Bash

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d '{"first_name":"Alice", "last_name":"Smith", "email_address":"alice@example.com", "password":"SecurePass123"}'
```

##### Windows CMD (Escape double quotes)

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d "{\"first_name\":\"Alice\", \"last_name\":\"Smith\", \"email_address\":\"alice@example.com\", \"password\":\"SecurePass123\"}"
```

This command should return a successful response (e.g. the created user record or a confirmation message).

## Production Deployment

### Docker Configuration

**Multi-stage Build**:
- Optimized dependency installation
- Non-root user for security
- Health check integration
- Minimal production image

**Security Features**:
- Non-root container execution
- Environment variable configuration
- Input validation and sanitization
- Sanitized generic error responses
- Secure password hashing (Argon2id)
- Verification required for high-risk actions (delete user, password and email update)
- UUID User ID, prevents predictable user enumeration
- Additional security measures intended for implementation in production deployment

### Monitoring & Health Checks

**Health Endpoint**:
- Database connectivity verification
- Service status reporting
- Version information
- Timestamp tracking

**Logging** (partially implemented):
- Structured logging with configurable levels
- Database operation tracking
- Error reporting with context
- Performance monitoring

### Scalability Considerations

**Database Optimization**:
- Proper indexing on foreign keys and lookup fields
- Additional indexing for complex query joins (e.g., cart operations with product enrichment)
- Batch processing for bulk operations
- Efficient query patterns with relationships

**Background Processing**:
- Scheduled task management with APScheduler
- Graceful shutdown handling
- Error recovery and retry logic
- Resource cleanup on termination

---

## Support

For technical support or questions about the Database Service, please refer to the project documentation or contact the development team.
