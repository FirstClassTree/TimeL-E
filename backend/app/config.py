# backend/app/config.py
import os
from typing import List, Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class Settings:
    NODE_ENV = os.getenv("NODE_ENV", "development")

    FRONTEND_PORT = os.getenv("FRONTEND_PORT", "3000")

    # Service URLs - can be overridden by environment variables
    DB_SERVICE_URL: str = os.getenv("DB_SERVICE_URL", "http://localhost:5001")
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "TimeL-E Backend API"
    VERSION: str = "1.0.0"
    
    # Development settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Request timeouts (seconds)
    SERVICE_TIMEOUT: int = int(os.getenv("SERVICE_TIMEOUT", "30"))

    # CORS Configuration
    CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "")
    
    @property
    def cors_allow_origins_list(self) -> List[str]:
        """Get validated CORS origins from environment variable"""
        if not self.CORS_ALLOW_ORIGINS:
            return []
        
        origins = []
        try:
            for origin in self.CORS_ALLOW_ORIGINS.split(","):
                origin = origin.strip()
                if origin:
                    try:
                        if self.validate_origin(origin):
                            origins.append(origin)
                        else:
                            logger.warning(f"Invalid CORS origin ignored: {origin}")
                    except Exception as e:
                        logger.error(f"Error validating CORS origin '{origin}': {str(e)}")
        except Exception as e:
            logger.error(f"Error processing CORS_ALLOW_ORIGINS environment variable: {str(e)}")
            return []  # Return empty list on critical error to prevent startup failure
        
        return origins
    
    def validate_origin(self, origin: str) -> bool:
        """Validate CORS origin format and security using proper URL parsing"""
        if not origin:
            return False
        
        try:
            parsed = urlparse(origin)
            
            # Must have valid scheme
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Must have hostname
            if not parsed.hostname:
                return False
            
            # Production should only allow HTTPS (except for actual localhost/127.0.0.1)
            if (self.NODE_ENV == "production" and 
                parsed.scheme == 'http' and 
                parsed.hostname not in ['localhost', '127.0.0.1']):
                return False
            
            # Block suspicious patterns in the full URL
            suspicious_patterns = ['javascript:', 'data:', 'file:', 'ftp:']
            if any(pattern in origin.lower() for pattern in suspicious_patterns):
                return False
            
            return True
            
        except Exception as e:
            # Invalid URL format
            logger.warning(f"Invalid URL format for origin validation: {origin}: {str(e)}")
            return False
    
    def build_cors_origins(self) -> List[str]:
        """Build CORS origins based on environment with proper validation"""
        origins = []
        
        try:
            if self.NODE_ENV == "production":
                # Production: Use environment variable with validation
                env_origins = self.cors_allow_origins_list
                if env_origins:
                    origins.extend(env_origins)
                    logger.info(f"Production CORS origins: {origins}")
                else:
                    logger.warning("No CORS origins configured for production - this may cause frontend connection issues")
            
            else:
                # Development: Build local origins
                protocols = ["http", "https"]
                hosts = ["localhost", "127.0.0.1"]
                ports = [self.FRONTEND_PORT, "5173"]  # Frontend port, Vite default
                
                # Remove duplicates while preserving order
                unique_ports = []
                for port in ports:
                    if port not in unique_ports:
                        unique_ports.append(port)
                
                for protocol in protocols:
                    for host in hosts:
                        for port in unique_ports:
                            origin = f"{protocol}://{host}:{port}"
                            origins.append(origin)
                
                logger.info(f"Development CORS origins configured: {len(origins)} origins for ports {unique_ports}")
        
        except Exception as e:
            logger.error(f"Error building CORS origins: {str(e)}")
            # Fallback to minimal safe configuration
            origins = [f"http://localhost:{self.FRONTEND_PORT}"]
            logger.warning(f"Using fallback CORS origin: {origins}")
        
        return origins

settings = Settings()

