"""
Pytest configuration for database integrity tests.

This module provides fixtures and configuration for testing database
constraints, foreign keys, and schema integrity.
"""

import pytest
import psycopg2
from ..users.conftest import POSTGRES_URL


@pytest.fixture
def db_connection():
    """
    Provide a PostgreSQL database connection for database testing.
    Connection is automatically closed after test completion.
    """
    conn = psycopg2.connect(POSTGRES_URL)
    try:
        yield conn
    finally:
        conn.close()
