"""
Common test helper functions for TimeL-E user routes testing.

This module provides utility functions that are used across multiple test files
for user management, data generation, and common assertions.
"""

import time
import requests
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List, Union, Mapping
import uuid
from dateutil.parser import parse

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    # Fallback if faker is not available
    class FakeFallback:
        def first_name(self): return "Test"
        def last_name(self): return "User"
        def phone_number(self): return "+1-555-0123"
        def street_address(self): return "123 Test St"
        def city(self): return "Test City"
        def postcode(self): return "12345"
        def country(self): return "Test Country"
    fake = FakeFallback()


def generate_unique_email(prefix: str = "test") -> str:
    """
    Generate a unique email address for testing.
    
    Args:
        prefix: Email prefix (default: "test")
        
    Returns:
        Unique email address with timestamp
    """
    return f"{prefix}_{uuid.uuid4().hex}@timele-test.com"


def generate_unique_password(prefix: str = "TestPass") -> str:
    """
    Generate a unique password for testing.
    
    Args:
        prefix: Password prefix (default: "TestPass")
        
    Returns:
        Unique password with timestamp
    """
    timestamp = int(time.time() * 1000)
    return f"{prefix}123_{timestamp}"


def create_test_user_data(
    email_prefix: str = "test",
    include_optional: bool = True,
    external_user_id: Optional[uuid.UUID] = None,
    **overrides
) -> Dict[str, Union[str, int, bool, datetime]]:
    """
    Create test user data with realistic values.
    
    Args:
        email_prefix: Prefix for email generation
        include_optional: Whether to include optional fields
        external_user_id: Optional pre-generated external user ID (UUID4)
        **overrides: Field overrides
        
    Returns:
        Dictionary containing test user data
    """
    timestamp = str(int(time.time() * 1000))
    
    base_data: Dict[str, Union[str, int, bool, datetime]] = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email_address": generate_unique_email(email_prefix),
        "password": generate_unique_password(),
        "external_user_id": str(external_user_id or uuid.uuid4())
    }
    
    if include_optional:
        optional_data: Dict[str, Union[str, int, bool, datetime]] = {
            "phone_number": fake.phone_number()[:15],  # Limit length
            "street_address": fake.street_address(),
            "city": fake.city(),
            "postal_code": fake.postcode(),
            "country": fake.country(),
            "days_between_order_notifications": 7,
            "order_notifications_via_email": True,
            "order_notifications_start_date_time": datetime.now(UTC).isoformat()
        }
        base_data.update(optional_data)
    
    # Apply any overrides
    for key, value in overrides.items():
        base_data[key] = value
    
    return base_data


def extract_user_id_from_response(response: requests.Response) -> Optional[str]:
    """
    Extract user ID from various response formats, prioritizing external UUID.
    
    Args:
        response: HTTP response containing user data
        
    Returns:
        User ID (external UUID4 string) if found, None otherwise
    """
    try:
        data = response.json()
        
        # Try different response structures
        if isinstance(data, dict):
            # Prioritize external UUID fields
            external_id_fields = [
                "externalUserId",  # Backend API
                "external_user_id",  # DB service
                "userId",  # Fallback to userId
            ]
            
            for field in external_id_fields:
                if field in data:
                    return str(data[field])
            
            # Check nested data structures
            if "data" in data:
                if isinstance(data["data"], dict):
                    for field in external_id_fields:
                        if field in data["data"]:
                            return str(data["data"][field])
                
                # Check list-based responses (DB service)
                if isinstance(data["data"], list) and data["data"]:
                    user_data = data["data"][0]
                    for field in external_id_fields:
                        if field in user_data:
                            return str(user_data[field])
        
        return None
    except (ValueError, KeyError, TypeError):
        return None


# Rest of the file remains the same as in the previous version

# Explicitly define what gets imported when using 'from test_helpers import *'
__all__ = [
    'generate_unique_email',
    'generate_unique_password',
    'create_test_user_data',
    'create_backend_user_data',
    'create_invalid_user_data',
    'create_notification_settings_data',
    'extract_user_id_from_response',
    'extract_user_email_from_response',
    'assert_datetime_close',
    'assert_user_data_matches',
    'assert_response_has_structure',
    'BaseUserTestContext',
    'DbServiceUserTestContext',
    'BackendUserTestContext',
    'UserTestContext',
    'cleanup_test_user',
    'PerformanceTimer',
    'measure_response_time'
]
