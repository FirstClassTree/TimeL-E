from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .config import settings
from sqlalchemy.exc import SQLAlchemyError

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_database_connection():
    """Attempts to connect and execute a trivial SQL to verify DB connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print("Database connection successful!")
        return True
    except SQLAlchemyError as e:
        print(f"Database connection failed: {e}")
        return False

