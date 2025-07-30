# backend/app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .routers import orders, predictions, users, cart, categories, products
from .models.base import APIResponse, ErrorResponse
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TimeL-E Grocery API - Backend API for grocery e-commerce with real CSV data",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Origin Validation Middleware
@app.middleware("http")
async def cors_validation_middleware(request: Request, call_next):
    """Validate CORS origins and log suspicious requests"""
    origin = request.headers.get("origin")
    if origin and not settings.validate_origin(origin):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Blocked suspicious CORS origin: {origin} from IP: {client_ip}")
        return JSONResponse(
            status_code=403,
            content={"error": "Origin not allowed", "code": "CORS_ORIGIN_BLOCKED"}
        )
    return await call_next(request)

# Build robust CORS origins
cors_origins = settings.build_cors_origins()

# Environment-specific CORS configuration
if settings.NODE_ENV == "production":
    cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers = [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ]
    cors_expose_headers = ["X-Total-Count", "X-Page-Count"]
    cors_max_age = 600  # Cache preflight for 10 minutes
else:
    cors_methods = ["*"]  # All methods for development
    cors_headers = ["*"]  # All headers for development
    cors_expose_headers = []
    cors_max_age = 0  # No caching in development

# Add CORS middleware with robust configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
    expose_headers=cors_expose_headers,
    max_age=cors_max_age,
)

# Log CORS configuration on startup
logger.info(f"CORS configured for {settings.NODE_ENV} environment")
logger.info(f"CORS origins: {len(cors_origins)} configured")
if settings.DEBUG:
    logger.debug(f"CORS origins list: {cors_origins}")

# Include routers with API prefix
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(orders.router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(cart.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)

# Root endpoint
@app.get("/")
async def root() -> APIResponse:
    """Root endpoint with API information"""
    data = {
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME,
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
        "endpoints": {
            "health": "/health",
            "api_routes": f"{settings.API_V1_PREFIX}/*"
        }
    }
    # Only include internal service URLs if in development
    if settings.NODE_ENV == "development":
        data["services"] = {
            "database": settings.DB_SERVICE_URL,
            "ml": settings.ML_SERVICE_URL
        }
    return APIResponse(
        message="TimeL-E Backend API Gateway",
        data=data
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
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    print(f"error {str(exc)}")
    print(traceback.format_exc())  # write to logs, not console in prod
    error_response = ErrorResponse(
        message="Internal server error",
        error_code="INTERNAL_ERROR",
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
