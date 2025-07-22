"""
Database Initialization Logic

This script creates the required schemas and tables in the database *only if they do not already exist*.
- If the database is empty (e.g., new volume), it creates all schemas and tables as defined in the SQLAlchemy models.
- If the database already contains these schemas and tables (e.g., persistent volume is mounted), this script makes no changes.
- Existing data is not modified, and no migrations or destructive actions are performed.
"""

from app.database import engine
from app.models.base import Base
from sqlalchemy import text

schemas = ["users", "products", "orders"]

def create_schemas():
    with engine.connect() as conn:
        for schema in schemas:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()

def init_db():
    # create the schemas users, products, and orders
    create_schemas()
    # generate the tables defined in the SQLAlchemy models under those schemas
    Base.metadata.create_all(bind=engine)

