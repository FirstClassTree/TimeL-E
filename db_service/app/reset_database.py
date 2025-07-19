#!/usr/bin/env python3
"""
Reset database and create fresh schema with integer user IDs
"""
from sqlalchemy import text
from .database import engine, SessionLocal
from .models.base import Base

def reset_database():
    """Drop all tables and recreate with integer schema"""
    print("🔄 Resetting database schema...")
    
    try:
        # Get a direct connection to execute raw SQL
        with engine.connect() as connection:
            # Drop all tables in all schemas
            print("🗑️ Dropping all existing tables...")
            
            # Drop tables in orders schema
            connection.execute(text("DROP SCHEMA IF EXISTS orders CASCADE"))
            
            # Drop tables in users schema  
            connection.execute(text("DROP SCHEMA IF EXISTS users CASCADE"))
            
            # Drop tables in products schema
            connection.execute(text("DROP SCHEMA IF EXISTS products CASCADE"))
            
            # Commit the drops
            connection.commit()
            
        print("✅ Database schemas dropped successfully")
        
        # Recreate all tables with new schema
        print("🏗️ Creating fresh database schema...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database schema recreated with integer IDs")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

if __name__ == "__main__":
    reset_database()
