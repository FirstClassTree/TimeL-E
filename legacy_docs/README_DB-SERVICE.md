# Database Service

## Overview

The **db-service** is a FastAPI microservice that acts as an internal **Database API Gateway**.  
It interfaces with a PostgreSQL database and exposes RESTful endpoints that are consumed by the main backend service.  
The backend sends HTTP requests to this service for database operations (CRUD + query),  
and the db-service translates them to SQLAlchemy operations.    
This allows backend to remain DB-agnostic, and enables swapping/replicating DBs via internal services.

## Responsibilities

- Connects to the PostgreSQL instance
- Defines ORM models for PostgreSQL
- Manages and initializes schemas using SQLAlchemy
- On initialization, populates the products schema in the database with data from CSV files (on mounted volume).
- Exposes generic RESTful endpoints to create, retrieve, update, delete, and list entities (users, products, orders)
- Exposes a `/query` endpoint for advanced queries
- Provides a `/health` endpoint for health checks
- Manages scheduler to trigger login and optional email notifications for scheduled orders.
- Manages all notification logic (order scheduling reminder, order status updates with automatic trigger for order status updates to be logged in OrderStatusHistory, active cart on login)

## Quick Start
After all services started with Docker,
```bash
docker-compose up --build
```
The API will be available at:  
- **API**: http://localhost:7000  
- **Interactive Docs**: http://localhost:7000/docs (in development mode)  
    a FastAPI web server that automatically generates and serves interactive API documentation for DB Service.
- **Health Check**: http://localhost:7000/health (in development mode)  

**Note**: Make sure .env is configured correctly with DB credentials.   

## How It Works
The backend service sends requests to this service.  
These are handled by db-service's internal routers utilizing SQLAlchemy to communicate with thr Postgres container.

## Directory Structure

```text
db_service/
├── app/
│   ├── main.py                     # FastAPI entrypoint with health check
│   ├── init_db.py                  # Initializes the PostgreSQL schemas
│   ├── database_service.py         # Defines API endpoints for DB access
│   ├── database.py                 # SQLAlchemy engine/session setup
│   ├── config.py                   # Environment/config loading
│   ├── populate_from_csv.py        # populate empty db with data from products.csv, aisles.csv, departments.csv
│   ├── populate_enriched_data.py   # populate db with enriched products data
│   ├── order_routs.py              # Defines API endpoints for DB access to orders
│   ├── user_routs.py               # Defines API endpoints for DB access to users
│   ├── reset_database.py           # drop all schemas with all tables
│   ├── __init__.py
│   └── models/                     # SQLAlchemy models
│       ├── __init__.py
│       └── base.py
│       └──orders.py
│       └──products.py
│       └──users.py
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── update_schema.sql
```

### Dual-ID Architecture Implementation

**The db_service utilizes a selective dual-ID architecture for optimal performance, scalability, and security:**

#### Users: Dual-ID Architecture
- **Internal IDs**: Numeric primary keys (`BIGSERIAL`) used internally for database operations and foreign key relationships
- **External IDs**: UUID4 strings exposed to the backend (and from there to the frontend) via API endpoints
- **Security Enhancement**: Prevents exposure of sequential integer IDs in URLs, eliminating enumeration attacks
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

### Architecture:
- User endpoints: `/api/users/{user_id}` (UUID4 string)
- Order endpoints: `/api/orders/{order_id}` (integer string)
- Cart endpoints: `/api/carts/{user_id}` (UUID4 string for user reference)
- All response fields: `user_id` (UUID4), `order_id` (integer), `cart_id` (integer)
- Internal database uses numeric IDs for optimal PostgreSQL performance

#### Overview
- **Users**: Dual-ID system with internal numeric PK + external UUID4 for security
- **Orders & Carts**: Simple integer IDs for performance and CSV data preservation
- UUID validation performed for user IDs at each endpoint
- Integer validation performed for order/cart IDs at each endpoint

### User ID Strategy: Legacy Users vs. New Users

#### Legacy Records (migrated from `users_demo.csv`)
- Internal Database Key: Integer (from original legacy data)
- API/Public ID (exposed as `user_id`):
- Deterministically generated using UUID5 (`uuid.uuid5`)
- Namespace is fixed for the application (e.g., `USER_UUID_NAMESPACE`)
- Formula:
```python
external_user_id = uuid.uuid5(USER_UUID_NAMESPACE, str(legacy_integer_id))
```

This ensures that the same legacy ID always maps to the same UUID, providing stable references for migration and testing.

#### New Records
- Internal Database Key: Integer (autoincrement)
- API/Public ID (exposed as `user_id`):
  - Randomly generated using UUID4 (`uuid.uuid4()`)
  - Recommended for all new users created after migration
```python
external_user_id = uuid.uuid4()
```
### Fast UUID Lookup with Database Indexing
- To make user lookups efficient via the public API, the `external_user_id` column is both unique and indexed.
- This allows instant retrieval by UUID, essential for APIs that never expose or use the internal numeric PK.



### Password generation and hashing

...





### Healthcheck

Docker Compose healthcheck is defined as:

```dockerfile
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}" ]
      interval: 5s
      timeout: 3s
      retries: 5
```

## Configuration

- CSV data population always runs at startup: The service will attempt to populate data from CSV files on each startup.  
If the tables already contain data, the process is skipped.
- For enriched products data, the script looks for all matching /data/products_enriched/enriched_products_dept*.csv files  
and only populates if the table is empty.
- Database reset is controlled via the environment variable `RESET_DATABASE_ON_STARTUP`:  
  Set `RESET_DATABASE_ON_STARTUP=true` in the `.env` to drop and fully recreate all schemas/tables on startup,  
ensuring a fresh state before loading CSV data. If false or unset, the existing database is preserved.

## Testing the API (Example)

Once the `db-service` is running via Docker and port `7000` is mapped,  
one can test if specific endpoints are exposed using curl.

### Example Request (`POST /users`)

Note: If the `/users` endpoint is not implemented yet in the FastAPI router,
this request will return `{"detail":"Not Found"}`.

Run from the **host machine**.

#### Linux / macOS / Git Bash

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d '{"first_name":"Alice", "last_name":"Smith", "email_address":"alice@example.com", "password":"SecurePass123"}'
```

#### Windows CMD (Escape double quotes)

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d "{\"first_name\":\"Alice\", \"last_name\":\"Smith\", \"email_address\":\"alice@example.com\", \"password\":\"SecurePass123\"}"
```

Once the `POST /users` route is implemented in db-service, this command should return a successful response
(e.g. the created user record or a confirmation message).


#### More Windows CMD Examples

```bash
curl -X POST http://localhost:7000/query -H "Content-Type: application/json" -d "{\"sql\": \"SELECT * FROM products.products LIMIT 1\", \"params\": []}"
```

```bash
curl -X POST http://localhost:7000/query -H "Content-Type: application/json" -d "{\"sql\": \"SELECT * FROM products.products WHERE department_id = $1 LIMIT $2\", \"params\": [19, 10]}"
```

**See test_db-service.py** for more.

## API Endpoints

### Custom Query ```/query```

Accepts parameterized SQL queries in PostgreSQL style (\$1, \$2, ...) with a list of parameters.

Expects ```JSON: { "sql": "SELECT ... WHERE ...", "params": [...] }```

Later should be restricted to `select queries` for `products` schema only.  

### Catalogue ```GET /products```

Returns a paginated list of products from the database with department and aisle names,  
optionally filtered by department (categories).

Full address for other containers:

`http://db-service:7000/products`

#### Has following query parameters:

* `limit` (default: 25, min: 1, max: 100); How many products to return.

* `offset` (default: 0, min: 0); Where to start (for pagination).

* `categories` (optional, can repeat); Filter by one or more department names (case-insensitive).

#### Example for host in development environment:

`http://localhost:7000/products?categories=Bakery&categories=Dairy`

`http://localhost:7000/products?limit=50&offset=100`

#### Backend example, with params:
```python
products_result = await db_service.list_entities(
    "products",
    {"limit": 25, "offset": 0, "categories": ["Bakery", "Dairy"]}
)
```

```python
products_result = await db_service.list_entities(
    "products",
    {"limit": limit, "offset": offset, "categories": categories}
)
```

### ORDER API Endpoints

### Create Order ```POST /orders```

Creates a new order in the database.  
**User IDs use UUIDv4. (See below).

Full address for other containers:

`http://db-service:7000/orders`

### Request Body (JSON):

```json
{
    "user_id": 1,
    "eval_set": "new",
    "order_dow": 1,
    "order_hour_of_day": 14,
    "days_since_prior_order": 7,
    "total_items": 3,
    "status": "pending",
    "phone_number": "123-456-7890",
    "street_address": "123 Main St",
    "city": "Springfield",
    "postal_code": "62701",
    "country": "USA",
    "tracking_number": "TRACK12345",
    "shipping_carrier": "UPS",
    "tracking_url": "http://example.com/track",
    "items": [
        {
            "product_id": 101,
            "quantity": 2,
            "add_to_cart_order": 1,
            "reordered": 0
        },
        {
            "product_id": 102,
            "quantity": 1,
            "add_to_cart_order": 2,
            "reordered": 0
        }
    ]
}
```

Example Request (Backend usage):

```python
order_request = {
    "user_id": 1,
    "eval_set": "new",
    "order_dow": 1,
    "order_hour_of_day": 14,
    "days_since_prior_order": 7,
    "total_items": 3,
    "status": "pending",
    "items": [
        {"product_id": 101, "quantity": 2},
        {"product_id": 102, "quantity": 1}
    ]
}
order_result = await db_service.create_order(order_request)
```

### Add Product to Order ```POST /orders/{order_id}/items```

Adds new products to an existing order.

If the order already contains the product, its quantity will be increased;
otherwise, a new item row is created.

Full address for other containers:

'http://db-service:7000/orders/{order_id}/items'

### Request Body (JSON):

```json
[
  {
    "product_id": 103,
    "quantity": 2,
    "add_to_cart_order": 3,
    "reordered": 0
  },
  {
    "product_id": 104,
    "quantity": 1
  }
]
```

#### Response:

```json
{
  "message": "Added 2 items to order f9de...53f8",
  "order_id": "f9de...53f8",
  "added_items": [
    {
      "order_id": "f9de...53f8",
      "product_id": 103,
      "quantity": 2,
      "add_to_cart_order": 3,
      "reordered": 0,
      "updated": false
    },
    {
      "order_id": "f9de...53f8",
      "product_id": 104,
      "quantity": 1,
      "add_to_cart_order": 4,
      "reordered": 0,
      "updated": false
    }
  ],
  "total_added": 2
}
```
### Example Request (Backend usage):

```python
order_id = "b2acaa2e-22d6-11ef-803b-63d8b24f7e8b"  # Example order UUID
items_to_add = [
    {"product_id": 101, "quantity": 2},
    {"product_id": 105, "quantity": 1, "reordered": 1}
]

result = await db_service.create_entity(
    entity_type=f"orders/{order_id}/items",
    data=items_to_add  # NOTE: Items are sent as a list, not wrapped in a dict
)
```

Note:

* Use create_entity(entity_type=..., data=...) for POST.

* entity_type should be "orders/{order_id}/items", no leading slash.

* data is a list of items, not a dict.

* This method is fully async; call with await.

### User API Endpoints

### Datetime handling and Timezones

Naive datetime (e.g., 2024-07-24T13:00:00)
* Assumed to be in UTC
* Automatically converted and marked as UTC (+00:00) internally

Timezone-aware datetime (e.g., 2024-07-24T13:00:00+02:00)
* Converted to UTC for consistency
* Stored and returned in UTC

This ensures:
* Reliable scheduling logic
* No ambiguity in user input
* Safer handling of dates regardless of client behavior

### Create User ```POST /users```

Creates new user with unique email address.
Names do not have to be unique and may be repeated.  
Password is hashed using bcrypt.

**User external IDs use UUIDv4:**  
UUIDv4 provides unique identifiers that are efficient for indexing and pagination.  
Unlike auto-increment integers, UUIDv4 values are highly resistant to guessing or enumeration,  
making the endpoints more secure, even if user IDs are exposed in URLs.  
also enables distributed ID generation across multiple servers without collisions. 

Params:    
* first_name, last_name, email_address, password, phone_number, street_address, city, postal_code, country  

Returns:  
* user_id, first_name, last_name, email_address

#### Example Request (Backend usage):

```python
user = db_service.create_entity(
    endpoint="/users/",
    data={
        "first_name": "Alice",
        "last_name": "Smith",
        "email_address": "alice@example.com",
        "password": "12345678",
        "phone_number": "555-1234",
        "street_address": "1 Main St",
        "city": "Townsville",
        "postal_code": "00001",
        "country": "Wonderland"
    }
)
```

### User Login ```POST /users/login```

Logs user in if the email and password are correct. Otherwise returns "Invalid email or password".  

#### Request Body (JSON):

```json
{
  "email_address": "alice@example.com",
  "password": "Password123"
}
```

#### Response:  
```json
{
  "user_id": 42,
  "first_name": "Alice",
  "last_name": "Smith",
  "email_address": "alice@example.com",
  "phone_number": "123-456-7890",
  "street_address": "1 Main St",
  "city": "Townsville",
  "postal_code": "00001",
  "country": "Wonderland",
  "days_between_order_notifications": 7,
  "order_notifications_start_date_time": "2025-07-24T14:00:00Z",
  "order_notifications_next_scheduled_time": "2025-07-31T14:00:00Z",
  "pending_order_notification": false,
  "order_notifications_via_email": true,
  "last_notification_sent_at": "2025-07-23T14:00:00Z"
}
```

#### Example Request (Backend usage):

```python
import requests

LOGIN_URL = "http://localhost:7000/users/login"

payload = {
    "email_address": "alice@example.com",
    "password": "Password123"
}

response = requests.post(LOGIN_URL, json=payload)

if response.status_code == 200:
    user_data = response.json()
    print("Login successful!")
    print(user_data)
else:
    print(f"Login failed: {response.status_code}")
    print(response.json())
```

### Update Password ```POST /users/{user_id}/password```

Updates the user's password. Requires current password for validation.

#### Example Request (Backend usage):

```python
db_service.create_entity(
    endpoint=f"/users/{user_id}/password",
    data={"current_password": "oldpw", "new_password": "newpw123"}
)
```

### Update Email ```POST /users/{user_id}/email```

Updates the user's email address.  
Requires current password for validation and ensures the new email is unique.
Returns updated email.

#### Example Request (Backend usage):

```python
db_service.create_entity(
    endpoint=f"/users/{user_id}/email",
    data={"current_password": "pw", "new_email_address": "new@email.com"}
)
```

Notes:
* If the current password is incorrect, the request will fail.
* The new email must not already exist in the database.
* For user security, email changes are not allowed via the general update endpoint (PUT /users/{user_id});  
this dedicated endpoint must be used.

### Fetch details ```GET /users/{user_id}```

Fetches user details by user_id (uuid7). Returns full details.except credentials

#### Example Request (Backend usage):

```python
user = db_service.get_entity(endpoint=f"/users/{user_id}")
```

### Update ```PUT /users/{user_id}```

Partially updates user fields. Only the provided fields will be updated.  
Cannot update email_address or password through this endpoint by default.  

#### Example Request (Backend usage):

```python
db_service.update_entity(
    endpoint=f"/users/{user_id}",
    data={"city": "Newtown", "phone_number": "555-9999"}
)
```

### Delete User ```DELETE /users/{user_id}```

Deletes a user. Requires current password for validation to prevent unauthorized deletion.

#### Example Request (Backend usage):

```python
db_service.delete_entity(
    endpoint=f"/users/{user_id}",
    data={"password": "currentpw"}
)
```

### Notifications API
Provides full control over user notification preferences via GET and PUT endpoints. Fully timezone-aware.  
Backed by a custom scheduler and real email delivery infrastructure for precise order reminders, even during development.    

#### Fields the user controls (via API input)
* `days_between_order_notifications`:	Frequency (in days) between reminders.
* `order_notifications_start_date_time`:	When the schedule begins (can be optional or default to now).
* `order_notifications_via_email`:	Whether user wants to opt in to receive reminders via email.

#### Fields the db_service controls:
* `order_notifications_next_scheduled_time`:	Calculated: start + (now - order_notifications_next_scheduled_time) // interval + 1
* `last_notification_sent_at`:	Set by scheduler when a notification is sent.
* `pending_order_notification`:	Set by scheduler if a notification is due and not sent yet.


### Update Notification Settings ```PUT /users/{user_id}/notification-settings```

Update notification settings for the user. Can send partial fields.  
The `order_notifications_start_date_time` field should be provided in ISO 8601 format with an explicit timezone offset  
(e.g., Z for UTC or +02:00, -05:00, etc.).

Examples (valid):
```json
"order_notifications_start_date_time": "2025-07-24T14:00:00Z"
"order_notifications_start_date_time": "2025-07-24T09:00:00-05:00"
```
* The service expects timezone-aware datetimes.
* If a datetime is submitted without a timezone, it is assumed to be UTC as a fallback.
* All datetimes are internally stored and returned as UTC with timezone awareness preserved.

#### Request Body (JSON):

```json
{
  "days_between_order_notifications": 7,
  "order_notifications_start_date_time": "2025-07-24T14:00:00Z",
  "order_notifications_via_email": true
}
```

#### Response:  
```json
{
  "message": "Notification settings updated successfully",
  "user_id": 206110,
  "days_between_order_notifications": 3,
  "order_notifications_start_date_time": "2025-07-25T02:56:42.889469+00:00",
  "order_notifications_next_scheduled_time": "2025-07-28T02:56:42.889469+00:00",
  "order_notifications_via_email": false,
  "pending_order_notification": false,
  "last_notification_sent_at": null
}
```

### Get Notification Settings ```GET /users/{user_id}/notification-settings```

Get notification settings for the user. Use to display upcoming schedules or missed reminders clearly.

#### Request Body (JSON):
n/a

#### Response:  
```json
{
  "user_id": 42,
  "days_between_order_notifications": 7,
  "order_notifications_start_date_time": "2025-07-24T14:00:00Z",
  "order_notifications_next_scheduled_time": "2025-07-31T14:00:00Z",
  "last_notification_sent_at": "2025-07-23T14:00:00Z",
  "pending_order_notification": false,
  "order_notifications_via_email": true
}
```


### Cart API Endpoints

These endpoints provide full CRUD (create, retrieve, update, delete) operations for user shopping carts.  
Each cart belongs to a specific user and contains a list of items (products with quantity).  
All product IDs must be valid (exist in the products table).  
The backend is responsible for ensuring only authenticated users can access their own carts.    

Note:
* All endpoints validate that the user exists.  
* All product IDs in requests are validated for existence.  
* Cart responses always return enriched product details (product_name, aisle, department, price, etc).  
* All changes update the cart’s updated_at timestamp (exposed in API, ISO8601 UTC).  
* All cart responses include `updated_at` timestamp.  
Clients can display or use this value to track last updates.  
* All Cart CRUD endpoints respond with the full Cart (including `updated_at`) except for DELETE, which returns a simple message.  
`updated_at` is always UTC and ISO8601 formatted.


### Create Cart ```POST /carts```

Creates a new cart for the given user. Fails if user does not exist or a cart already exists for that user  
or the new cart contains product_ids that do not exist in the products table.  
Returns HTTP `409` if cart already exists for the user.  

#### Request Body (JSON):

```json
{
  "user_id": 1234,
  "items": [
    {
      "product_id": 42,
      "quantity": 3
    },
    {
      "product_id": 99,
      "quantity": 1
    }
  ]
}
```

#### Response:

```json
{
  "user_id": 1234,
  "items": [
    {
      "product_id": 42,
      "quantity": 3,
      "product_name": "Banana",
      "aisle_name": "Fruit",
      "department_name": "Produce",
      "description": "Fresh bananas",
      "price": 0.25,
      "image_url": "https://img/banana.png"
    },
    {
      "product_id": 99,
      "quantity": 1,
      "product_name": "Milk",
      "aisle_name": "Dairy",
      "department_name": "Dairy",
      "description": "Whole milk",
      "price": 2.99,
      "image_url": "https://img/milk.png"
    }
  ],
  "total_items": 2,
  "total_quantity": 4,
  "updated_at": "2024-07-16T17:20:10.532588+00:00"
}
```

#### Example Request (Backend usage):

```python
from ..models.base import Cart, CartItem

# Build the Cart object in backend
cart = Cart(
    user_id=1234,
    items=[
        CartItem(product_id=42, quantity=3),
        CartItem(product_id=99, quantity=1),
    ]
)
# Create the cart for the user
result = await db_service.create_entity(
    endpoint="/carts/",
    data=cart.model_dump()
)
```

### Get Cart ```GET /carts/{user_id}```

Fetches the cart for a specific user.  
If no cart exists, returns empty cart with the current timestamp. 

#### Response:

```json
{
  "user_id": 1234,
  "items": [
    {
      "product_id": 42,
      "quantity": 3,
      "product_name": "Banana",
      "aisle_name": "Fruit",
      "department_name": "Produce",
      "description": "Fresh bananas",
      "price": 0.25,
      "image_url": "https://img/banana.png"
    }
  ],
  "total_items": 1,
  "total_quantity": 3,
  "updated_at": "2024-07-16T17:20:10.532588+00:00"
}
```

#### Example Request (Backend usage):

```python
user_id = 1234
cart = await db_service.get_entity("carts", user_id)

# cart is a dict matching the CartResponse model
```

#### Example Request (curl):

```bash
curl -X GET http://localhost:7000/carts/1234
```

### Update/Replace Cart ```PUT /carts/{user_id}```

Replaces the entire cart for a user (full upsert/replace operation).  
If a cart does not exist, creates a new one. Returns enriched product details and the latest `updated_at`.  

#### Request Body (JSON):

```json
{
  "user_id": 1234,
  "items": [
    {
      "product_id": 42,
      "quantity": 2
    }
  ]
}
```

#### Response:  
same format as "Get Cart" above, with `updated_at`.

#### Example Request (Backend usage):

```python
from ..models.base import Cart, CartItem

cart = Cart(
    user_id=1234,
    items=[
        CartItem(product_id=42, quantity=2),
    ]
)
result = await db_service.update_entity(
    "carts", 1234, cart.model_dump()
)
```

### Delete Cart ```DELETE /carts/{user_id}```
Deletes a user's cart.  
Returns HTTP 404 if the user or the cart do not exist.  

#### Response:

```json
{ "message": "Cart deleted successfully for user 1234" }
```

#### Example Request (Backend usage):

```python
await db_service.delete_entity("carts", user_id)
```

##########################################################

\# TODO:

add_cart_item(user_id, item) → POST /carts/{user_id}/items – add an item (or increment if exists)


update_cart_item(user_id, product_id, qty) → PUT /carts/{user_id}/items/{product_id} – set quantity for item (update/remove)


remove_cart_item(user_id, product_id) → DELETE /carts/{user_id}/items/{product_id} – remove item


clear_user_cart(user_id) → DELETE /carts/{user_id}} – clear cart


checkout_cart(user_id) → POST /carts/{user_id}/checkout – convert cart to order


### Create Cart ```POST /carts```

...

#### Request Body (JSON):

```json
```

#### Response:

```json
```

#### Example Request (Backend usage):

```python
```

### Create Cart ```POST /carts```

...

#### Request Body (JSON):

```json
```

#### Response:

```json
```

#### Example Request (Backend usage):

```python
```

### Full Example for Cart API (Backend usage):

```python
# Create a new cart for user
cart_data = {
    "user_id": 1234,
    "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 4, "quantity": 1}
    ]
}
resp = await db_service.create_entity(endpoint="/carts/", data=cart_data)

# Get cart
resp = await db_service.get_entity("carts", user_id)

# Update (replace) cart
cart_data["items"].append({"product_id": 7, "quantity": 3})
resp = await db_service.update_entity("carts", user_id, cart_data)

# Delete cart
await db_service.delete_entity("carts", user_id)
```

---

## Orders API

### Get Order Details ```GET /orders/{order_id}```

Get detailed order information with full tracking info, enriched products, and status history.

#### URL Parameters:
- `order_id` (required): Integer order ID

#### Response:

```json
{
  "success": true,
  "message": "Order 3422001 details retrieved successfully",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "order_number": 5,
      "order_dow": 1,
      "order_hour_of_day": 14,
      "days_since_prior_order": 7,
      "total_items": 3,
      "total_price": 24.97,
      "status": "shipped",
      "delivery_name": "John Doe",
      "phone_number": "+1-555-1234",
      "street_address": "123 Main St",
      "city": "New York",
      "postal_code": "10001",
      "country": "US",
      "tracking_number": "1Z999AA1234567890",
      "shipping_carrier": "UPS",
      "tracking_url": "https://www.ups.com/track?tracknum=1Z999AA1234567890",
      "invoice": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:45:00Z",
      "items": [
        {
          "product_id": 123,
          "product_name": "Organic Milk",
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0,
          "price": 4.99,
          "description": "Fresh organic whole milk from grass-fed cows",
          "image_url": "https://example.com/images/organic-milk.jpg",
          "department_name": "Dairy Eggs",
          "aisle_name": "Milk"
        }
      ],
      "status_history": [
        {
          "history_id": 1,
          "order_id": "3422001",
          "status": "pending",
          "changed_at": "2024-01-15T10:30:00Z",
          "changed_by": null,
          "note": "Order created"
        },
        {
          "history_id": 2,
          "order_id": "3422001",
          "status": "processing",
          "changed_at": "2024-01-15T12:00:00Z",
          "changed_by": "system",
          "note": "Order processing started"
        },
        {
          "history_id": 3,
          "order_id": "3422001",
          "status": "shipped",
          "changed_at": "2024-01-15T14:45:00Z",
          "changed_by": "fulfillment_center",
          "note": "Package shipped via UPS"
        }
      ]
    }
  ]
}
```

#### Error Responses:
- 400: "Invalid order ID format" (for non-integer order IDs)
- 404: "Order not found"
- 500: "Database error occurred"

#### Example Request (curl):

```bash
curl -X GET http://localhost:7000/orders/3422001
```

#### Example Request (Backend usage):

```python
# Get detailed order information
order_result = await db_service.get_entity("orders", "3422001")

if order_result.get("success"):
    order_data = order_result.get("data", [])[0]
    print(f"Order {order_data['order_id']} status: {order_data['status']}")
    print(f"Items: {len(order_data['items'])}")
    print(f"Status history: {len(order_data['status_history'])} changes")
```

### Get User Orders ```GET /orders/user/{user_id}```

Get paginated order history for a specific user with enriched item details.

#### URL Parameters:
- `user_id` (required): UUID4 user ID

#### Query Parameters:
- `limit` (optional): Number of orders to return (1-100, default: 20)
- `offset` (optional): Number of orders to skip (default: 0)

#### Response:

```json
{
  "success": true,
  "message": "Found 2 orders for user 550e8400-e29b-41d4-a716-446655440000",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "order_number": 5,
      "total_items": 3,
      "total_price": 24.97,
      "status": "pending",
      "delivery_name": "John Doe",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "items": [
        {
          "product_id": 123,
          "product_name": "Organic Milk",
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0,
          "price": 4.99,
          "description": "Fresh organic whole milk from grass-fed cows",
          "image_url": "https://example.com/images/organic-milk.jpg",
          "department_name": "Dairy Eggs",
          "aisle_name": "Milk"
        }
      ]
    }
  ]
}
```

#### Example Request (curl):

```bash
curl -X GET "http://localhost:7000/orders/user/550e8400-e29b-41d4-a716-446655440000?limit=10&offset=0"
```

### Create Order ```POST /orders```

Create a new order with items. Orders are always created with "pending" status.

#### Request Body (JSON):

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "order_dow": 1,
  "order_hour_of_day": 14,
  "days_since_prior_order": 7,
  "delivery_name": "John Doe",
  "phone_number": "+1-555-1234",
  "street_address": "123 Main St",
  "city": "New York",
  "postal_code": "10001",
  "country": "US",
  "items": [
    {
      "product_id": 123,
      "quantity": 2,
      "add_to_cart_order": 1,
      "reordered": 0
    }
  ]
}
```

#### Response:

```json
{
  "success": true,
  "message": "Order created successfully",
  "data": [
    {
      "order_id": "3422001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "order_number": 1,
      "status": "pending",
      "total_items": 1,
      "delivery_name": "John Doe",
      "phone_number": "+1-555-1234",
      "street_address": "123 Main St",
      "city": "New York",
      "postal_code": "10001",
      "country": "US",
      "created_at": "2025-01-05T17:30:00Z",
      "updated_at": "2025-01-05T17:30:00Z",
      "items": [
        {
          "product_id": 123,
          "product_name": "Organic Milk",
          "quantity": 2,
          "add_to_cart_order": 1,
          "reordered": 0,
          "price": 4.99,
          "description": "Fresh organic whole milk from grass-fed cows",
          "image_url": "https://example.com/images/organic-milk.jpg",
          "department_name": "Dairy Eggs",
          "aisle_name": "Milk"
        }
      ]
    }
  ]
}
```

#### Example Request (Backend usage):

```python
# Create a new order
order_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "delivery_name": "John Doe",
    "phone_number": "+1-555-1234",
    "street_address": "123 Main St",
    "city": "New York",
    "postal_code": "10001",
    "country": "US",
    "items": [
        {
            "product_id": 123,
            "quantity": 2,
            "add_to_cart_order": 1,
            "reordered": 0
        }
    ]
}

order_result = await db_service.create_entity("orders", order_data)
```

### Key Features:

- Uses UUID4 for user references, integer IDs for orders
- Enriched Product Data: Full product details including descriptions, images, department/aisle info
- Status History: Complete chronological tracking of order status changes
- Tracking Integration: Support for tracking numbers, carriers, and URLs
- Invoice Support: Binary invoice data storage and retrieval
- Delivery Information: Complete shipping address and delivery name support
- Pagination: Efficient order-level pagination for user order history
