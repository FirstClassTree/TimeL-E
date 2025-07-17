from fastapi import FastAPI
from contextlib import asynccontextmanager
from .init_db import init_db
from .database_service import router
from .users_routers import router as users_router
from .orders_routers import router as orders_router
import os
from .populate_from_csv import populate_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup
    init_db()
    # load data from departments.csv, aisles.csv, and products.csv into their respective tables
    populate_tables()
    yield       # App runs
    # Optionally add shutdown logic after yield

app = FastAPI(
    description="Database Service - exposes a RESTful API and internally communicates with a PostgreSQL database",
    lifespan=lifespan
)
app.include_router(router)
app.include_router(users_router)
app.include_router(orders_router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("DB_SERVICE_PORT", 7000))  # fallback to 7000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)