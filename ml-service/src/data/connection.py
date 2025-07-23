# ml-service/src/data/connection.py
# Database connection utilities for ML service

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://timely_user:timely_password@postgres:5432/timely_db")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_database_connection() -> bool:
    """Test if database connection is working."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
        return False

@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def get_db():
    """Dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
