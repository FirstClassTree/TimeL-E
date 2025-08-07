"""
Pytest configuration and shared fixtures for TimeL-E user routes testing.

This module provides:
- Test environment configuration
- Shared fixtures for HTTP clients and database connections
- Common test utilities and setup/teardown logic
- Service availability checking
"""

import os
import time
import pytest
import requests
from datetime import datetime, UTC
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import psycopg2 - required for database testing
try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    try:
        import psycopg2_binary as psycopg2
        import psycopg2_binary.extensions as psycopg2_extensions
        # Create alias for compatibility
        psycopg2.extensions = psycopg2_extensions
    except ImportError:
        raise ImportError(
            "psycopg2 is required for database testing. "
            "Install with: pip install psycopg2-binary"
        )

# Test environment configuration
DB_SERVICE_URL = os.getenv("TEST_DB_SERVICE_URL", "http://localhost:7000")
BACKEND_URL = os.getenv("TEST_BACKEND_URL", "http://localhost:8000")
POSTGRES_URL = os.getenv("TEST_POSTGRES_URL", "postgresql://timele_user:timele_password@localhost:5432/timele_db")

# Test timeouts and retries
SERVICE_TIMEOUT = 30  # seconds
SERVICE_CHECK_INTERVAL = 1  # seconds
REQUEST_TIMEOUT = 10  # seconds


class TestConfig:
    """Test configuration constants"""
    DB_SERVICE_URL = DB_SERVICE_URL
    BACKEND_URL = BACKEND_URL
    POSTGRES_URL = POSTGRES_URL
    REQUEST_TIMEOUT = REQUEST_TIMEOUT


def wait_for_service(url: str, timeout: int = SERVICE_TIMEOUT) -> bool:
    """
    Wait for a service to become available.
    
    Args:
        url: Service URL to check
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if service is available, False otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/docs", timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(SERVICE_CHECK_INTERVAL)
    return False


@pytest.fixture(scope="session", autouse=True)
def check_services():
    """
    Ensure all required services are available before running tests.
    This fixture runs automatically for all test sessions.
    """
    print("\nChecking service availability...")
    
    # Check DB Service
    if not wait_for_service(DB_SERVICE_URL):
        pytest.fail(f"DB Service not available at {DB_SERVICE_URL}")
    print(f"✓ DB Service available at {DB_SERVICE_URL}")
    
    # Check Backend Service
    if not wait_for_service(BACKEND_URL):
        pytest.fail(f"Backend Service not available at {BACKEND_URL}")
    print(f"✓ Backend Service available at {BACKEND_URL}")
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        conn.close()
        print(f"✓ PostgreSQL available")
    except psycopg2.Error as e:
        pytest.fail(f"PostgreSQL not available: {e}")
    except Exception as e:
        pytest.fail(f"PostgreSQL connection failed: {e}")


@pytest.fixture(scope="session")
def db_service_url() -> str:
    """DB Service base URL for direct testing"""
    return DB_SERVICE_URL


@pytest.fixture(scope="session")
def backend_url() -> str:
    """Backend Service base URL for integration testing"""
    return BACKEND_URL


@pytest.fixture(scope="session")
def postgres_url() -> str:
    """PostgreSQL connection URL"""
    return POSTGRES_URL


@pytest.fixture
def db_connection() -> Generator:
    """
    Provide a PostgreSQL database connection for direct database testing.
    Connection is automatically closed after test completion.
    """
    conn = psycopg2.connect(POSTGRES_URL)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def db_session() -> Generator:
    """
    Provide a SQLAlchemy session for ORM testing.
    Session is automatically closed and rolled back after test completion.
    """
    engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def unique_timestamp() -> str:
    """Generate a unique timestamp for test data"""
    return str(int(time.time() * 1000))


@pytest.fixture
def test_user_data(unique_timestamp: str) -> Dict[str, Any]:
    """
    Generate test user data with unique identifiers.
    
    Returns:
        Dictionary containing test user data suitable for user creation
    """
    return {
        "first_name": "Test",
        "last_name": "User",
        "email_address": f"test_user_{unique_timestamp}@timele-test.com",
        "password": f"TestPassword123_{unique_timestamp}",
        "phone_number": f"555-{unique_timestamp[-4:]}",
        "street_address": f"{unique_timestamp} Test Street",
        "city": "Test City",
        "postal_code": f"{unique_timestamp[:5]}",
        "country": "Test Country",
        "days_between_order_notifications": 7,
        "order_notifications_via_email": True,
        "order_notifications_start_date_time": datetime.now(UTC).isoformat()
    }


@pytest.fixture
def minimal_user_data(unique_timestamp: str) -> Dict[str, Any]:
    """
    Generate minimal test user data with only required fields.
    
    Returns:
        Dictionary containing minimal user data for testing required field validation
    """
    return {
        "first_name": "Minimal",
        "last_name": "User",
        "email_address": f"minimal_user_{unique_timestamp}@timele-test.com",
        "password": f"MinimalPass123_{unique_timestamp}"
    }


@pytest.fixture
def backend_user_data(unique_timestamp: str) -> Dict[str, Any]:
    """
    Generate test user data in backend API format (with field aliases).
    
    Returns:
        Dictionary containing test user data suitable for backend API calls
    """
    return {
        "firstName": "Backend",
        "lastName": "User",
        "email": f"backend_user_{unique_timestamp}@timele-test.com",
        "password": f"BackendPass123_{unique_timestamp}",
        "phone": f"555-{unique_timestamp[-4:]}",
        "street_address": f"{unique_timestamp} Backend Street",
        "city": "Backend City",
        "postal_code": f"{unique_timestamp[:5]}",
        "country": "Backend Country"
    }


@pytest.fixture
def invalid_user_data() -> Dict[str, Any]:
    """
    Generate invalid test user data for negative testing.
    
    Returns:
        Dictionary containing invalid user data
    """
    return {
        "first_name": "",  # Empty required field
        "last_name": "",   # Empty required field
        "email_address": "invalid-email",  # Invalid email format
        "password": "123",  # Too short password
        "days_between_order_notifications": 500  # Out of range value
    }


class TestUserManager:
    """
    Helper class for managing test users throughout test lifecycle.
    Provides methods for creating, tracking, and cleaning up test users.
    """
    
    def __init__(self):
        self.created_users = []
    
    def track_user(self, user_id: int, email: str):
        """Track a created user for cleanup"""
        self.created_users.append({"user_id": user_id, "email": email})
    
    def cleanup_all(self, db_service_url: str):
        """Clean up all tracked users"""
        for user in self.created_users:
            try:
                # Attempt to delete user (may fail if already deleted)
                requests.delete(
                    f"{db_service_url}/users/{user['user_id']}", 
                    json={"password": "any"},  # Password may not match, but attempt cleanup
                    timeout=REQUEST_TIMEOUT
                )
            except:
                pass  # Ignore cleanup failures
        self.created_users.clear()


@pytest.fixture
def user_manager() -> Generator[TestUserManager, None, None]:
    """
    Provide a user manager for tracking and cleaning up test users.
    Automatically cleans up all tracked users after test completion.
    """
    manager = TestUserManager()
    yield manager
    manager.cleanup_all(DB_SERVICE_URL)


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """
    Make an HTTP request with standard timeout and error handling.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Request URL
        **kwargs: Additional arguments passed to requests
        
    Returns:
        Response object
    """
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    return requests.request(method, url, **kwargs)


def assert_success_response(response: requests.Response, expected_status: int = 200):
    """
    Assert that a response indicates success.
    
    Args:
        response: HTTP response to check
        expected_status: Expected HTTP status code
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )


def assert_error_response(response: requests.Response, expected_status: int, expected_error: str | None = None):
    """
    Assert that a response indicates an error.
    
    Args:
        response: HTTP response to check
        expected_status: Expected HTTP status code
        expected_error: Expected error message substring (optional)
    """
    assert response.status_code == expected_status, (
        f"Expected error status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    if expected_error:
        response_text = response.text.lower()
        expected_error_lower = expected_error.lower()
        assert expected_error_lower in response_text, (
            f"Expected error message containing '{expected_error}', "
            f"got: {response.text}"
        )


def assert_user_response_structure(user_data: Dict[str, Any], check_sensitive: bool = False):
    """
    Assert that user response data has the expected structure.
    
    Args:
        user_data: User data dictionary to validate
        check_sensitive: Whether to check for absence of sensitive data
    """
    # Required fields
    required_fields = [
        "user_id", "first_name", "last_name", "email_address"
    ]
    
    for field in required_fields:
        assert field in user_data, f"Missing required field: {field}"
        assert user_data[field] is not None, f"Field {field} should not be None"
    
    # Sensitive fields should not be present
    if check_sensitive:
        sensitive_fields = ["password", "hashed_password"]
        for field in sensitive_fields:
            assert field not in user_data, f"Sensitive field {field} should not be in response"


def assert_notification_settings_structure(settings_data: Dict[str, Any]):
    """
    Assert that notification settings response has the expected structure.
    
    Args:
        settings_data: Notification settings data to validate
    """
    expected_fields = [
        "user_id", "days_between_order_notifications", 
        "order_notifications_via_email", "pending_order_notification"
    ]
    
    for field in expected_fields:
        assert field in settings_data, f"Missing notification setting field: {field}"
    
    # Validate data types and ranges
    if settings_data.get("days_between_order_notifications"):
        days = settings_data["days_between_order_notifications"]
        assert 1 <= days <= 365, f"Invalid notification interval: {days}"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "db_service: marks tests for db_service direct testing"
    )
    config.addinivalue_line(
        "markers", "backend: marks tests for backend integration testing"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location"""
    for item in items:
        # Mark tests based on file path
        if "db_service" in str(item.fspath):
            item.add_marker(pytest.mark.db_service)
        elif "backend" in str(item.fspath):
            item.add_marker(pytest.mark.backend)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if item.name and ("load" in item.name or "performance" in item.name):
            item.add_marker(pytest.mark.slow)
