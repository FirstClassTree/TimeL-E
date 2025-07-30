"""
Common test helper functions for TimeL-E user routes testing.

This module provides utility functions that are used across multiple test files
for user management, data generation, and common assertions.
"""

import time
import requests
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
import uuid

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
    # timestamp = int(time.time() * 1000)
    # return f"{prefix}_user_{timestamp}@timele-test.com"
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
    **overrides
) -> Dict[str, Any]:
    """
    Create test user data with realistic values.
    
    Args:
        email_prefix: Prefix for email generation
        include_optional: Whether to include optional fields
        **overrides: Field overrides
        
    Returns:
        Dictionary containing test user data
    """
    timestamp = str(int(time.time() * 1000))
    
    base_data = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email_address": generate_unique_email(email_prefix),
        "password": generate_unique_password(),
    }
    
    if include_optional:
        base_data.update({
            "phone_number": fake.phone_number()[:15],  # Limit length
            "street_address": fake.street_address(),
            "city": fake.city(),
            "postal_code": fake.postcode(),
            "country": fake.country(),
            "days_between_order_notifications": 7,
            "order_notifications_via_email": True,
            "order_notifications_start_date_time": datetime.now(UTC).isoformat()
        })
    
    # Apply any overrides
    base_data.update(overrides)
    
    return base_data


def create_backend_user_data(
    email_prefix: str = "backend",
    include_optional: bool = True,
    **overrides
) -> Dict[str, Any]:
    """
    Create test user data in backend API format (with field aliases).
    
    Args:
        email_prefix: Prefix for email generation
        include_optional: Whether to include optional fields
        **overrides: Field overrides
        
    Returns:
        Dictionary containing test user data for backend API
    """
    base_data = {
        "firstName": fake.first_name(),
        "lastName": fake.last_name(),
        "email": generate_unique_email(email_prefix),
        "password": generate_unique_password(),
    }
    
    if include_optional:
        base_data.update({
            "phone": fake.phone_number()[:15],
            "street_address": fake.street_address(),
            "city": fake.city(),
            "postal_code": fake.postcode(),
            "country": fake.country()
        })
    
    # Apply any overrides
    base_data.update(overrides)
    
    return base_data


def create_invalid_user_data() -> Dict[str, Any]:
    """
    Create invalid user data for negative testing.
    
    Returns:
        Dictionary containing invalid user data
    """
    return {
        "first_name": "",  # Empty required field
        "last_name": "",   # Empty required field
        "email_address": "invalid-email-format",  # Invalid email
        "password": "123",  # Too short
        "days_between_order_notifications": 500,  # Out of range
        "phone_number": "x" * 100,  # Too long
    }


def create_notification_settings_data(**overrides) -> Dict[str, Any]:
    """
    Create notification settings test data.
    
    Args:
        **overrides: Field overrides
        
    Returns:
        Dictionary containing notification settings data
    """
    base_data = {
        "days_between_order_notifications": 14,
        "order_notifications_via_email": True,
        "order_notifications_start_date_time": datetime.now(UTC).isoformat()
    }
    
    base_data.update(overrides)
    return base_data


def extract_user_id_from_response(response: requests.Response) -> Optional[int]:
    """
    Extract user ID from various response formats.
    
    Args:
        response: HTTP response containing user data
        
    Returns:
        User ID if found, None otherwise
    """
    try:
        data = response.json()
        
        # Try different response structures
        if isinstance(data, dict):
            # Direct user_id field
            if "user_id" in data:
                return int(data["user_id"])
            
            # ServiceResponse format with data array
            if "data" in data and isinstance(data["data"], list) and data["data"]:
                user_data = data["data"][0]
                if "user_id" in user_data:
                    return int(user_data["user_id"])
            
            # APIResponse format with data object
            if "data" in data and isinstance(data["data"], dict):
                if "user_id" in data["data"]:
                    return int(data["data"]["user_id"])
        
        return None
    except (ValueError, KeyError, TypeError):
        return None


def extract_user_email_from_response(response: requests.Response) -> Optional[str]:
    """
    Extract user email from various response formats.
    
    Args:
        response: HTTP response containing user data
        
    Returns:
        User email if found, None otherwise
    """
    try:
        data = response.json()
        
        # Try different response structures
        if isinstance(data, dict):
            # Direct email_address field
            if "email_address" in data:
                return data["email_address"]
            
            # ServiceResponse format with data array
            if "data" in data and isinstance(data["data"], list) and data["data"]:
                user_data = data["data"][0]
                if "email_address" in user_data:
                    return user_data["email_address"]
            
            # APIResponse format with data object
            if "data" in data and isinstance(data["data"], dict):
                if "email_address" in data["data"]:
                    return data["data"]["email_address"]
        
        return None
    except (ValueError, KeyError, TypeError):
        return None


def wait_for_condition(
    condition_func,
    timeout: int = 10,
    interval: float = 0.5,
    error_message: str = "Condition not met within timeout"
) -> bool:
    """
    Wait for a condition to become true.
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        error_message: Error message if timeout is reached
        
    Returns:
        True if condition was met, False if timeout
        
    Raises:
        TimeoutError: If condition is not met within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    raise TimeoutError(error_message)


def assert_datetime_close(
    dt1_str: str,
    dt2_str: str,
    tolerance_seconds: int = 5,
    message: str | None = None
):
    """
    Assert that two datetime strings are close to each other.
    
    Args:
        dt1_str: First datetime string
        dt2_str: Second datetime string
        tolerance_seconds: Maximum allowed difference in seconds
        message: Custom assertion message
    """
    from dateutil.parser import parse
    
    dt1 = parse(dt1_str)
    dt2 = parse(dt2_str)
    
    diff_seconds = abs((dt1 - dt2).total_seconds())
    
    if message is None:
        message = f"Datetimes {dt1_str} and {dt2_str} differ by {diff_seconds}s (tolerance: {tolerance_seconds}s)"
    
    assert diff_seconds <= tolerance_seconds, message


def assert_user_data_matches(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    ignore_fields: List[str] | None = None
):
    """
    Assert that user data matches expected values.
    
    Args:
        actual: Actual user data
        expected: Expected user data
        ignore_fields: Fields to ignore in comparison
    """
    if ignore_fields is None:
        ignore_fields = ["user_id", "password", "hashed_password"]
    
    for key, expected_value in expected.items():
        if key in ignore_fields:
            continue
            
        assert key in actual, f"Missing field: {key}"
        
        actual_value = actual[key]
        
        # Handle datetime fields specially
        if key.endswith("_time") or key.endswith("_date_time"):
            if expected_value and actual_value:
                assert_datetime_close(actual_value, expected_value)
        else:
            assert actual_value == expected_value, (
                f"Field {key}: expected {expected_value}, got {actual_value}"
            )


def assert_response_has_structure(
    response_data: Dict[str, Any],
    required_fields: List[str],
    optional_fields: List[str] | None = None,
    forbidden_fields: List[str] | None = None
):
    """
    Assert that response data has the expected structure.
    
    Args:
        response_data: Response data to validate
        required_fields: Fields that must be present
        optional_fields: Fields that may be present
        forbidden_fields: Fields that must not be present
    """
    if optional_fields is None:
        optional_fields = []
    if forbidden_fields is None:
        forbidden_fields = []
    
    # Check required fields
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"
        assert response_data[field] is not None, f"Required field {field} is None"
    
    # Check forbidden fields
    for field in forbidden_fields:
        assert field not in response_data, f"Forbidden field {field} is present"
    
    # Validate that all present fields are either required or optional
    allowed_fields = set(required_fields + optional_fields)
    for field in response_data.keys():
        assert field in allowed_fields, f"Unexpected field: {field}"


def cleanup_test_user(
    user_id: int,
    password: str,
    db_service_url: str,
    ignore_errors: bool = True
) -> bool:
    """
    Clean up a test user by deleting it.
    
    Args:
        user_id: User ID to delete
        password: User password for verification
        db_service_url: DB service base URL
        ignore_errors: Whether to ignore deletion errors
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        response = requests.delete(
            f"{db_service_url}/users/{user_id}",
            json={"password": password},
            timeout=10
        )
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = response.json()
        
        # Consider cleanup successful if:
        # 1. User was successfully deleted (success=True)
        # 2. User was not found (success=False with "not found" error - already deleted)
        if response_json.get("success", False):
            return True
        elif "not found" in response_json.get("error", "").lower():
            return True  # User already deleted, cleanup successful
        else:
            return False  # Other errors (wrong password, etc.)
            
    except Exception as e:
        if not ignore_errors:
            raise
        return False


def get_test_user_by_email(
    email: str,
    db_service_url: str
) -> Optional[Dict[str, Any]]:
    """
    Find a test user by email address (for debugging/verification).
    Note: This requires direct database access or a search endpoint.
    
    Args:
        email: Email address to search for
        db_service_url: DB service base URL
        
    Returns:
        User data if found, None otherwise
    """
    # This would require a search endpoint or direct database access
    # For now, return None as the current API doesn't support user search
    return None


class BaseUserTestContext:
    """
    Base context manager for test user lifecycle management.
    Provides common functionality for different service types.
    """
    
    def __init__(
        self,
        service_url: str,
        user_data: Dict[str, Any] | None = None,
        auto_cleanup: bool = True
    ):
        self.service_url = service_url
        self.user_data = user_data or create_test_user_data()
        self.auto_cleanup = auto_cleanup
        self.user_id = None
        self.password = self.user_data.get("password")
        self.created = False
    
    def __enter__(self):
        """Create the test user - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement __enter__")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the test user - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement __exit__")
    
    def get_user_id(self) -> int:
        """Get the created user ID"""
        if not self.user_id:
            raise RuntimeError("User not created or creation failed")
        return self.user_id
    
    def get_password(self) -> str:
        """Get the user password"""
        if self.password is None:
            raise RuntimeError("Password not available")
        return self.password
    
    def get_email(self) -> str:
        """Get the user email"""
        return self.user_data["email_address"]


class DbServiceUserTestContext(BaseUserTestContext):
    """
    Context manager for db_service direct testing.
    Handles structured responses: {"success": bool, "data": [...], "error": str}
    """
    
    def __enter__(self):
        """Create the test user via db_service"""
        response = requests.post(
            f"{self.service_url}/users/",
            json=self.user_data,
            timeout=10
        )
        
        # DB service returns structured response, not HTTP status codes for business logic
        response_json = response.json()
        if response_json.get("success", False):
            self.user_id = extract_user_id_from_response(response)
            self.created = True
        else:
            error_msg = response_json.get("error", "Unknown error")
            raise RuntimeError(f"Failed to create test user: {error_msg}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the test user via db_service"""
        if self.auto_cleanup and self.created and self.user_id and self.password:
            cleanup_test_user(
                self.user_id,
                self.password,
                self.service_url,
                ignore_errors=True
            )


class BackendUserTestContext(BaseUserTestContext):
    """
    Context manager for backend API testing.
    Handles HTTP status codes (200, 201, 400, etc.)
    """
    
    def __enter__(self):
        """Create the test user via backend API"""
        # Convert to backend format if needed
        backend_data = self._convert_to_backend_format(self.user_data)
        
        response = requests.post(
            f"{self.service_url}/users/register",
            json=backend_data,
            timeout=10
        )
        
        # Backend returns HTTP status codes
        if response.status_code in [200, 201]:
            self.user_id = extract_user_id_from_response(response)
            self.created = True
        else:
            raise RuntimeError(f"Failed to create test user: {response.text}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the test user via backend API"""
        if self.auto_cleanup and self.created and self.user_id and self.password:
            try:
                # Backend user deletion (if endpoint exists)
                delete_data = {"password": self.password}
                requests.delete(
                    f"{self.service_url}/users/{self.user_id}",
                    json=delete_data,
                    timeout=10
                )
            except Exception:
                # Ignore cleanup errors for backend tests
                pass
    
    def _convert_to_backend_format(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert db_service format to backend API format"""
        backend_data = user_data.copy()
        
        # Map field names if needed (db_service uses email_address, backend might use email)
        if "email_address" in backend_data:
            backend_data["email"] = backend_data.pop("email_address")
        
        # Map other fields as needed
        field_mapping = {
            "first_name": "firstName",
            "last_name": "lastName",
            "phone_number": "phone"
        }
        
        for old_field, new_field in field_mapping.items():
            if old_field in backend_data:
                backend_data[new_field] = backend_data.pop(old_field)
        
        return backend_data


# Backward compatibility - keep UserTestContext as alias to DbServiceUserTestContext
UserTestContext = DbServiceUserTestContext


# Performance measurement utilities
class PerformanceTimer:
    """Simple performance timer for measuring test execution times"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def stop(self):
        """Stop timing"""
        self.end_time = time.time()
        return self
    
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        end = self.end_time or time.time()
        return end - self.start_time
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def measure_response_time(func, *args, **kwargs) -> tuple:
    """
    Measure the response time of a function call.
    
    Args:
        func: Function to measure
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Tuple of (result, elapsed_time_seconds)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time
    
    return result, elapsed_time
