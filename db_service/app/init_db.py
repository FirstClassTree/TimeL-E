"""
Database Initialization Logic

This script creates the required schemas and tables in the database *only if they do not already exist*.
- If the database is empty (e.g., new volume), it creates all schemas and tables as defined in the SQLAlchemy models.
- If the database already contains these schemas and tables (e.g., persistent volume is mounted), this script makes no changes.
- Existing data is not modified, and no migrations or destructive actions are performed.
"""

from app.db_core.database import engine
from app.db_core.models.base import Base
from sqlalchemy import text

schemas = ["users", "products", "orders"]

def create_schemas():
    with engine.connect() as conn:
        for schema in schemas:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()

def create_order_status_history_trigger():
    trigger_sql = """
    CREATE OR REPLACE FUNCTION orders.log_order_status_change() RETURNS TRIGGER AS $$
    DECLARE
        changed_by_user INTEGER;
    BEGIN
        changed_by_user := NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER;
        
        IF NEW.status IS DISTINCT FROM OLD.status THEN
            INSERT INTO orders.order_status_history (
                order_id,
                old_status,
                new_status,
                changed_at,
                changed_by,
                note
            )
            VALUES (
                NEW.order_id,
                OLD.status,
                NEW.status,
                NOW(),
                changed_by_user,
                NULL
            );
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_order_status_change ON orders.orders;
    CREATE TRIGGER trg_order_status_change
    AFTER UPDATE OF status ON orders.orders  -- trigger only when status changes
    FOR EACH ROW
    EXECUTE FUNCTION orders.log_order_status_change();
    """
    
    with engine.connect() as conn:
        conn.execute(text(trigger_sql))
        conn.commit()

def init_db():
    # create the schemas users, products, and orders
    create_schemas()
    # generate the tables defined in the SQLAlchemy models under those schemas
    Base.metadata.create_all(bind=engine)

    create_order_status_history_trigger()
