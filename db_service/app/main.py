"""
FastAPI application for the database service.
- Handles database reset (optional, via env variable)
- Initializes schemas/tables on startup
- Populates data from CSV files
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from .init_db import init_db
from .database_service import router
from .users_routers import router as users_router
from .orders_routers import router as orders_router
from .carts_routers import router as carts_router
from .inject_schema_docs import router as schema_doc_router
import os
import sys
import datetime
from .populate_from_csv import populate_tables
from .populate_enriched_data import populate_enriched_data
from .db_core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup

    print("Starting Database Service...")
    
    if settings.RESET_DATABASE_ON_STARTUP:
        from .reset_database import reset_database
        print("RESET_DATABASE_ON_STARTUP is true, resetting database...")
        if reset_database():
            print("Database reset successful")
        else:
            print("Database reset failed, trying with existing schema...")

    print("Initializing schemas/tables...")
    try:
        init_db()
    except Exception as e:
        print(f"CRITICAL ERROR during schema/table initialization: {e}")
        sys.exit(1)  # Immediately kill the process so container restarts/fails

    # load data from departments.csv, aisles.csv, products.csv, and users.csv into their respective tables (function will skip if already populated)
    try:
        populate_tables()
    except Exception as e:
        print(f"Error while populating tables from CSV: {e}")

    # load enriched product data from enriched_products_dept*.csv (function will skip if already populated)
    try:
        populate_enriched_data()
    except Exception as e:
        print(f"Error while populating enriched product data: {e}")
    
    print(f"Database Service ready! ({datetime.datetime.now().isoformat(timespec='seconds')})")

    yield       # App runs
    # Optionally add shutdown logic after yield

app = FastAPI(
    title="Database Service Api and Database Description",
    description="Database Service - exposes a RESTful API and internally communicates with a PostgreSQL database",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)
app.include_router(router)
app.include_router(users_router)
app.include_router(orders_router)
app.include_router(carts_router)
app.include_router(schema_doc_router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("DB_SERVICE_PORT", 7000))  # fallback to 7000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
