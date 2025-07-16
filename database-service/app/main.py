from fastapi import FastAPI
from app.database_service import router
import os

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("DB_SERVICE_PORT", 7000))  # fallback to 7000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)