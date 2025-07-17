# db-service

The **db-service** is a FastAPI microservice that acts as an internal **Database API Gateway**.

It interfaces with a PostgreSQL database and exposes RESTful endpoints that are consumed by the main backend service.

The backend sends HTTP requests to this service for database operations (CRUD + query), and the db-service translates them to SQLAlchemy operations.

This allows backend to remain DB-agnostic, and enables swapping/replicating DBs via internal services.

## Responsibilities

- Connects to the PostgreSQL instance
- Manages and initializes schemas using SQLAlchemy
- Defines ORM models for PostgreSQL
- Exposes generic RESTful endpoints to create, retrieve, update, delete, and list entities (users, products, orders)
- Exposes a `/query` endpoint for advanced queries
- Provides a `/health` endpoint for health checks

## Directory Structure

```text
db_service/
├── app/
│   ├── main.py                 # FastAPI entrypoint with health check
│   ├── init_db.py              # Initializes the PostgreSQL schemas
│   ├── database_service.py     # Defines API endpoints for DB access
│   ├── database.py             # SQLAlchemy engine/session setup
│   ├── config.py               # Environment/config loading
│   ├── populate_from_csv.py    # populate empty db with data from products.csv, aisles.csv, departments.csv
│   ├── __init__.py
│   └── models/                 # SQLAlchemy models
│       ├── __init__.py
│       └── base.py
│       └──orders.py
│       └──products.py
│       └──users.py
├── Dockerfile
├── .dockerignore
└── requirements.txt
```

## How It Works

The backend service sends requests to this service.

These are handled by db-service's internal router and routed to the appropriate model.

## API Endpoints

```/query```

Accepts parameterized SQL queries in PostgreSQL style ($1, $2, ...) with a list of parameters.
Expects JSON: { "sql": "SELECT ... WHERE ...", "params": [...] }
Later should be restricted to select queries only.  

```/products```

Returns a paginated list of products from the database with department and aisle names,
optionally filtered by department (categories).

Full address for other containers:

`http://db-service:7000/products`

Has the following query parameters:

* limit (default: 25, min: 1, max: 100) — How many products to return

* offset (default: 0, min: 0) — Where to start (for pagination)

* categories (optional, can repeat) — Filter by one or more department names (case-insensitive)

Example for host in development environment:
`http://localhost:7000/products?categories=Bakery&categories=Dairy`
`http://localhost:7000/products?limit=50&offset=100`

Backend example, with params:
```bash
products_result = await db_service.list_entities(
    "products",
    {"limit": 25, "offset": 0, "categories": ["Bakery", "Dairy"]}
)
```

```/orders```

Creates a new order in the database.

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

```bash
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

## Running the Service

Run the following command to start all services, including db-service:

```bash
docker-compose up --build
```

Make sure .env is configured correctly with DB credentials.

### Healthcheck

Docker Compose healthcheck is defined as:

```
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}" ]
      interval: 5s
      timeout: 3s
      retries: 5
```

## Testing the API (Example)

Once the `db-service` is running via Docker and port `7000` is mapped, one can test if specific endpoints are exposed using curl.

### Example Request (`POST /users`)

Note: If the `/users` endpoint is not implemented yet in the FastAPI router,
this request will return `{"detail":"Not Found"}`.

Run from the **host machine**.

#### Windows CMD (Escape double quotes)

```bash
curl -X POST http://localhost:7000/users -H "Content-Type: application/json" -d "{\"username\":\"alice\", \"email\":\"alice@example.com\"}"
```
#### Linux / macOS / Git Bash

```
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

also see test_db-service.py
