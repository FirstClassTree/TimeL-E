# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import orders, predictions, users, cart, categories, products
from .models.base import APIResponse

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TimeL-E Grocery API - Backend API for grocery e-commerce with real CSV data",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(predictions.router)
app.include_router(users.router)
app.include_router(cart.router)
app.include_router(categories.router)

# Root endpoint
@app.get("/")
async def root() -> APIResponse:
    """Root endpoint with API information"""
    return APIResponse(
        message="TimeL-E Backend API Gateway",
        data={
            "version": settings.VERSION,
            "project": settings.PROJECT_NAME,
            "docs": "/docs",
            "services": {
                "database": settings.DB_SERVICE_URL,
                "ml": settings.ML_SERVICE_URL
            }
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> APIResponse:
    """Simple health check for the API gateway"""
    return APIResponse(
        message="API Gateway is healthy",
        data={
            "status": "healthy",
            "version": settings.VERSION
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return HTTPException(
        status_code=500,
        detail=f"Internal server error: {str(exc)}"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
