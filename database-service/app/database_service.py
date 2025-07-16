# app/database_service.py

from fastapi import APIRouter
import psycopg2
import os

router = APIRouter()

DATABASE_URL = os.environ.get("DATABASE_URL")

@router.get("/health")
def health_check():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return {"status": "ok", "database": "reachable"}
    except Exception as e:
        return {"status": "error", "database": str(e)}