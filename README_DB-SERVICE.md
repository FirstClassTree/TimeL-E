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

TBD

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
