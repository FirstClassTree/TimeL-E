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
import sys
import datetime
from .populate_from_csv import populate_tables
from .populate_enriched_data import populate_enriched_data
from .db_core.config import settings
from .scheduler import process_scheduled_user_notifications
from apscheduler.schedulers.background import BackgroundScheduler
import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"

logging.basicConfig(
    level=logging.DEBUG if settings.NODE_ENV == "development" else logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    force=True  # Ensures this config applies, even if other libs set logging.
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup

    logging.info("Starting Database Service...")
    
    if settings.RESET_DATABASE_ON_STARTUP:
        from .reset_database import reset_database
        logging.info("RESET_DATABASE_ON_STARTUP is true, resetting database...")
        if reset_database():
            logging.info("Database reset successful")
        else:
            logging.warning("Database reset failed, trying with existing schema...")

    logging.info("Initializing schemas/tables...")
    try:
        init_db()
    except Exception as e:
        logging.critical(f"CRITICAL ERROR during schema/table initialization: {e}")
        sys.exit(1)  # Immediately kill the process so container restarts/fails

    # load data from departments.csv, aisles.csv, products.csv, and users.csv into their respective tables (function will skip if already populated)
    try:
        populate_tables()
    except Exception as e:
        logging.error(f"Error while populating tables from CSV: {e}")

    # load enriched product data from enriched_products_dept*.csv (function will skip if already populated)
    try:
        populate_enriched_data()
    except Exception as e:
        logging.error(f"Error while populating enriched product data: {e}")

    logging.info(f"Database Service ready! ({datetime.datetime.now().isoformat(timespec='seconds')})")

    logging.info("Starting notifications scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        process_scheduled_user_notifications,
        "interval",
        hours=1,
        id="user_notifications",
        replace_existing=True
    )
    scheduler.start()

    try:
        yield       # App runs
    # shutdown logic after yield
    finally:
        logging.info("Shutting down notifications scheduler...")
        scheduler.shutdown(wait=False)

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
async def health() -> dict:
    """Combined health check for DB service API and database connectivity."""

    # Database connection check
    db_status = "unreachable"
    db_error = None
    api_status = "unhealthy"
    try:
        import psycopg2
        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.close()
        db_status = "reachable"
        api_status = "healthy"
    except Exception as e:
        logging.error(f"Database health check failed: {str(e)}")
        db_error = str(e)

    resp = {
        "message": (
            "DB service API Gateway is healthy"
            if api_status == "healthy"
            else "DB service API Gateway cannot reach DB"
        ),
        "data": {
            "status": api_status,
            "version": settings.VERSION,
            "timestamp": datetime.datetime.now().isoformat(),
            "service": "database-service",
            "database": db_status
        }
    }
    # Only show error if in local/dev
    if settings.NODE_ENV == "development" and db_error:
        resp["data"]["db_error"] = db_error
    return resp


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.DB_SERVICE_PORT, reload=False)
