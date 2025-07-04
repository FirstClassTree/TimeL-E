# backend/app/config.py
import os
from typing import Optional

class Settings:
    # Service URLs - can be overridden by environment variables
    DB_SERVICE_URL: str = os.getenv("DB_SERVICE_URL", "http://localhost:5001")
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:5002")
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "TimeL-E Backend API"
    VERSION: str = "1.0.0"
    
    # Development settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Request timeouts (seconds)
    SERVICE_TIMEOUT: int = int(os.getenv("SERVICE_TIMEOUT", "30"))

settings = Settings()
