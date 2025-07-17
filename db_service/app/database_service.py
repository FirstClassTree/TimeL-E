# app/database_service.py

from fastapi import APIRouter, HTTPException, Request
import psycopg2
import os
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy import text
import asyncpg

router = APIRouter()

DATABASE_URL = os.environ.get("DATABASE_URL")

def validate_params(params):
    """Reject malformed inputs or strange usage."""
    if not isinstance(params, list):
        raise ValueError("Params must be a list")
    for p in params:
        if isinstance(p, (dict, list, set, tuple, bytes, bytearray)):
            raise ValueError(f"Disallowed param type: {type(p)}")
        if callable(p):
            raise ValueError("Function values not allowed in params")
        if isinstance(p, str) and len(p) > 10000:
            raise ValueError("String parameter too long")

@router.get("/health")
def health_check():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return {"status": "ok", "database": "reachable"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

@router.post("/query")
async def run_query(request: Request):
    """
    Accepts parameterized SQL queries in PostgreSQL style ($1, $2, ...) with a list of parameters.
    Expects JSON: { "sql": "SELECT ... WHERE ...", "params": [...] }
    """
    # """
    # Accepts parameterized SQL SELECT queries in PostgreSQL style ($1, $2, ...) with a list of parameters.
    # Expects JSON: { "sql": "SELECT ... WHERE ...", "params": [...] }
    # Only SELECT queries are allowed.
    # """
    body = await request.json()
    sql = body.get("sql")
    params = body.get("params", [])

    if not sql:
        raise HTTPException(status_code=400, detail="Missing 'sql' in request body")

    # if not sql.strip().lower().startswith("select"):
    #     raise HTTPException(status_code=403, detail="Only SELECT queries are allowed")

    try:
        validate_params(params) # protects against malformed inputs or strange usage
        # asyncpg expects $1/$2, but parameters should be passed as *args
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(sql, *params)
            # Convert Record objects to dicts for JSON serialization
            results = [dict(row) for row in rows]
        except Exception as query_exc:
            print(f"Query failed: {query_exc}")   # print goes to container logs
            raise HTTPException(status_code=400, detail=f"Database query failed.")
        finally:
            await conn.close()
        return {"status": "ok", "results": results}
    except Exception as e:
        print(f"Request failed: {e}")
        raise HTTPException(status_code=400, detail=f"Request failed.")

