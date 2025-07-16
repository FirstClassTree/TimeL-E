from fastapi import FastAPI
from contextlib import asynccontextmanager
from .init_db import init_db
from .database_service import router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # Runs once at startup
    yield       # App runs
    # Optionally add shutdown logic after yield

app = FastAPI(
    description="Database Service - exposes a RESTful API and internally communicates with a PostgreSQL database",
    lifespan=lifespan
)
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("DB_SERVICE_PORT", 7000))  # fallback to 7000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)