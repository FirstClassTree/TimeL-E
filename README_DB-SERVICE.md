# db-service

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

## How It Works

The backend service sends requests to this service.

These are handled by db-service's internal router and routed to the appropriate model.

## Running the Service

Run the following command to start all services, including db-service:

```bash
docker-compose up --build
```

Make sure .env is configured correctly with DB credentials.

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

- **CSV data population always runs at startup**: The service will attempt to populate data from CSV files on each startup.  
If the tables already contain data, the process is skipped.
- **Database reset is controlled via the environment variable `RESET_DATABASE_ON_STARTUP`**:  
  Set `RESET_DATABASE_ON_STARTUP=true` in the `.env` to drop and fully recreate all schemas/tables on startup,  
ensuring a fresh state before loading CSV data. If false or unset, the existing database is preserved.

## Testing the API (Example)

Once the `db-service` is running via Docker and port `7000` is mapped,  
one can test if specific endpoints are exposed using curl.

### Example Request (`POST /users`)

Note: If the `/users` endpoint is not implemented yet in the FastAPI router,
this request will return `{"detail":"Not Found"}`.

Run from the **host machine**.

#### Windows CMD (Escape double quotes)

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d "{\"username\":\"alice\", \"email\":\"alice@example.com\"}"
```
#### Linux / macOS / Git Bash

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d '{"username":"alice", "email":"alice@example.com"}'
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

### ORDER API Endpoints

```POST /orders```

Creates a new order in the database.  
**User IDs use UUIDv7. (See below).

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

```POST /orders/{order_id}/items```

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

Response:

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

### Create User ```POST /users```

Creates new user with unique email and username.  
Password is hashed using bcrypt.

**User IDs use UUIDv7:**  
UUIDv7 provides sortable, time-ordered, unique identifiers that are efficient for indexing and pagination.  
Unlike auto-increment integers, UUIDv7 values are highly resistant to guessing or enumeration,  
making the endpoints more secure, even if user IDs are exposed in URLs.  
also enables distributed ID generation across multiple servers without collisions, while maintaining chronological order. 

Params:    
* name, email_address, password, phone_number, street_address, city, postal_code, country  

Returns:  
* user_id, name, email_address

#### Example Request (Backend usage):

```python
user = db_service.create_entity(
    endpoint="/users/",
    data={
        "name": "Alice",
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


### Update Password ```POST /{user_id}/password```

Updates the user's password. Requires current password for validation.

#### Example Request (Backend usage):

```python
db_service.create_entity(
    endpoint=f"/users/{user_id}/password",
    data={"current_password": "oldpw", "new_password": "newpw123"}
)
```

### Fetch details ```GET /{user_id}```

Fetches user details by user_id (uuid7).

#### Example Request (Backend usage):

```python
user = db_service.get_entity(endpoint=f"/users/{user_id}")
```

### Update ```PATCH /{user_id}```

Partially updates user fields. Only the provided fields will be updated.

#### Example Request (Backend usage):

```python
db_service.update_entity(
    endpoint=f"/users/{user_id}",
    data={"city": "Newtown", "phone_number": "555-9999"}
)
```

### Delete User ```DELETE /{user_id}```

Deletes a user. Requires current password for validation to prevent unauthorized deletion.

#### Example Request (Backend usage):

```python
db_service.delete_entity(
    endpoint=f"/users/{user_id}",
    data={"password": "currentpw"}
)
```
