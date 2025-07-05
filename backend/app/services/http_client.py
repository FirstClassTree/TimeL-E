# backend/app/services/http_client.py
"""
Service clients for external service communication.
This module imports and re-exports service clients for convenience.
"""

from .base_client import ServiceClient
from .database_service import DatabaseService, db_service
from .ml_service import MLService, ml_service

# Re-export for backward compatibility and convenience
__all__ = [
    'ServiceClient',
    'DatabaseService', 
    'db_service',
    'MLService',
    'ml_service'
]
