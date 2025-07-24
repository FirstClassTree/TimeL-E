#!/usr/bin/env python3
"""
Reset database by dropping all relevant schemas and their contents.

This script drops the 'products', 'users', and 'orders' schemas from the database (with CASCADE),
removing all tables and objects in those schemas. It does **not** create schemas or tables,
that is handled separately in `init_db.py`.

Use this script to fully reset the database state.
"""
from sqlalchemy import text
from .database import engine

def reset_database():
    """
    Drop the 'products', 'users', and 'orders' schemas and all their tables and objects.
    """
    print("Resetting database schema...")
    
    try:
        # Get a direct connection to execute raw SQL
        with engine.connect() as connection:
            # Drop all tables in all schemas
            print("Dropping schemas: products, users, orders...")

            connection.execute(text("DROP SCHEMA IF EXISTS products CASCADE"))
            connection.execute(text("DROP SCHEMA IF EXISTS users CASCADE"))
            connection.execute(text("DROP SCHEMA IF EXISTS orders CASCADE"))
            connection.commit()
            
        print("Database schemas dropped successfully")
        return True
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False

if __name__ == "__main__":
    reset_database()
