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
    create_schemas()
    Base.metadata.create_all(bind=engine)
