# TimeL-E User Routes Test Suite

This directory contains tests specifically for user information flow through the TimeL-E system: Frontend → Backend `/users` endpoints → DB Service → Database.

## Scope

**What belongs here:**
- Tests for backend `/users` endpoints (registration, login, profile management)
- Tests for db_service `/users` endpoints (direct user operations)
- User-specific workflow integration tests
- User data model validation

**What does NOT belong here:**
- General database FK constraint testing (moved to `tests/database/`)
- Non-user API endpoints (belong in respective service test directories)
- General database utilities (moved to `tests/utils/`)

## Architecture & Test Strategy

```
Frontend → Backend /users (port 8000) → DB Service /users (port 7000) → PostgreSQL (port 5432)
```

### Test Layers

1. **Backend Tests**: Test backend `/users` endpoints that route to db_service
2. **DB Service Tests**: Test db_service `/users` endpoints directly  
3. **Integration Tests**: End-to-end user workflows and cross-service communication
4. **Utils**: User-specific test helpers and utilities

## Test Structure

```
tests/users/
├── README.md                           # This file
├── conftest.py                         # Pytest configuration and shared fixtures
├── requirements.txt                    # Test dependencies
├── db_service/
│   ├── __init__.py
│   ├── test_users_direct.py           # Direct db_service HTTP tests
│   ├── test_users_models.py           # SQLAlchemy + Pydantic model tests
│   └── test_users_business_logic.py   # Business logic validation
├── backend/
│   ├── __init__.py
│   ├── test_users_api.py              # Backend HTTP tests
│   ├── test_users_models.py           # Backend Pydantic model tests
│   └── test_error_handling.py         # Error transformation tests
├── integration/
│   ├── __init__.py
│   ├── test_full_workflows.py         # End-to-end user scenarios
│   └── test_service_communication.py  # Cross-service reliability
└── utils/
    ├── __init__.py
    ├── test_helpers.py                # Common test utilities
    ├── db_helpers.py                  # Database test helpers
    └── api_helpers.py                 # API testing utilities
```

## Test Coverage Matrix

### DB Service User Routes (Direct Tests - Port 7000)

| Endpoint | Method | Test Cases | Status |
|----------|--------|------------|--------|
| `/users/` | POST | ✅ Valid creation, ❌ Duplicate email, ❌ Invalid data | Complete |
| `/users/{id}` | GET | ✅ Valid retrieval, ❌ Not found | Complete |
| `/users/{id}` | PUT | ✅ Partial update, ✅ Full update, ❌ Not found | Complete |
| `/users/{id}` | DELETE | ✅ Valid deletion, ❌ Wrong password, ❌ Not found | Complete |
| `/users/login` | POST | ✅ Valid login, ❌ Invalid credentials | Complete |
| `/users/{id}/password` | PUT | ✅ Valid change, ❌ Wrong current password | Complete |
| `/users/{id}/email` | PUT | ✅ Valid change, ❌ Duplicate email, ❌ Wrong password | Complete |
| `/users/{id}/notification-settings` | GET | ✅ Valid retrieval, ❌ Not found | Complete |
| `/users/{id}/notification-settings` | PUT | ✅ Valid update, ❌ Invalid range | Complete |

### Backend User Routes (Integration Tests - Port 8000)

| Endpoint | Method | Test Cases | Status |
|----------|--------|------------|--------|
| `/users/login` | GET | ✅ Demo login functionality | Complete |
| `/users/login` | POST | ✅ Real login via db_service | Complete |
| `/users/{id}` | GET | ✅ Profile via db_service, ❌ Service errors | Complete |
| `/users/register` | POST | ✅ Registration via db_service, ❌ Service errors | Complete |
| `/users/{id}` | PUT | ✅ Update via db_service, ❌ Service errors | Complete |
| `/users/{id}` | DELETE | ✅ Deletion via db_service, ❌ Service errors | Complete |
| `/users/{id}/password` | PUT | ✅ Password change via db_service | Complete |
| `/users/{id}/email` | PUT | ✅ Email change via db_service | Complete |
| `/users/{id}/notification-settings` | GET | ✅ Settings via db_service | Complete |
| `/users/{id}/notification-settings` | PUT | ✅ Settings update via db_service | Complete |

### Model Tests

| Component | Test Cases | Status |
|-----------|------------|--------|
| SQLAlchemy User Model | Field validation, constraints, relationships | Complete |
| DB Service Pydantic Models | Request/response validation, serialization | Complete |
| Backend Pydantic Models | API model validation, field aliases | Complete |
| Business Logic | Notification scheduling, password hashing | Complete |

### Integration Tests

| Scenario | Test Cases | Status |
|----------|------------|--------|
| Complete User Lifecycle | Register → Login → Update → Delete | Complete |
| Password Change Workflow | Full password change flow with validation | Complete |
| Email Change Workflow | Full email change flow with validation | Complete |
| Notification Management | Settings management workflow | Complete |
| Service Communication | Backend ↔ DB service reliability | Complete |
| Error Scenarios | Service failures, timeouts, invalid responses | Complete |

## Setup Instructions

### Prerequisites

1. **Start Services**: Ensure all services are running
   ```bash
   docker-compose up -d
   ```

2. **Verify Service Availability**:
   - Backend: http://localhost:8000/docs
   - DB Service: http://localhost:7000/docs
   - PostgreSQL: localhost:5432

3. **Install Test Dependencies**:
   ```bash
   pip install -r tests/users/requirements.txt
   ```

### Environment Configuration

Tests run against the development environment using exposed ports:

```python
# Default configuration
DB_SERVICE_URL = "http://localhost:7000"
BACKEND_URL = "http://localhost:8000"
POSTGRES_URL = "postgresql://timele_user:timele_password@localhost:5432/timele_db"
```

Override with environment variables if needed:
```bash
export TEST_DB_SERVICE_URL="http://localhost:7000"
export TEST_BACKEND_URL="http://localhost:8000"
export TEST_POSTGRES_URL="postgresql://timele_user:timele_password@localhost:5432/timele_db"
```

## Running Tests

### Individual Test Files
```bash
# DB Service direct tests
pytest tests/users/db_service/test_users_direct.py -v

# Backend integration tests  
pytest tests/users/backend/test_users_api.py -v

# Model validation tests
pytest tests/users/db_service/test_users_models.py -v

# Full integration workflows
pytest tests/users/integration/test_full_workflows.py -v
```

### Test Categories
```bash
# All DB service tests
pytest tests/users/db_service/ -v

# All backend tests
pytest tests/users/backend/ -v

# All integration tests
pytest tests/users/integration/ -v

# All tests
pytest tests/users/ -v
```

### With Coverage
```bash
# Generate coverage report
pytest tests/users/ --cov=db_service --cov=backend --cov-report=html

# View coverage
open htmlcov/index.html
```

### Specific Test Patterns
```bash
# Run only creation tests
pytest tests/users/ -k "create" -v

# Run only error handling tests
pytest tests/users/ -k "error" -v

# Run only authentication tests
pytest tests/users/ -k "login or auth" -v
```

## Test Data Management

### User Test Data Strategy
- **Unique Identifiers**: Tests use timestamp-based unique emails to avoid conflicts
- **Cleanup**: Each test cleans up created users to maintain database state
- **Isolation**: Tests are independent and can run in any order
- **Fixtures**: Shared test data creation through pytest fixtures

### Database State
- Tests use the same PostgreSQL instance as development
- Test users are created with predictable patterns for easy identification
- Cleanup ensures no test data pollution

## Test Utilities

### Common Helpers (`tests/users/utils/test_helpers.py`)
- `generate_unique_email()`: Creates timestamp-based unique emails
- `create_test_user()`: Standard test user creation
- `cleanup_test_user()`: User cleanup after tests
- `assert_user_response()`: Validate user response structure

### API Helpers (`tests/users/utils/api_helpers.py`)
- `make_request()`: Standardized HTTP request handling
- `assert_http_error()`: Validate error responses
- `wait_for_service()`: Service availability checking

### Database Helpers (`tests/users/utils/db_helpers.py`)
- `get_db_connection()`: Database connection for direct queries
- `verify_user_exists()`: Database-level user verification
- `cleanup_test_data()`: Bulk test data cleanup

## Performance Benchmarks

### Response Time Targets
- User creation: < 500ms
- User login: < 200ms
- Profile retrieval: < 100ms
- Profile updates: < 300ms

### Load Testing
- Concurrent user operations: 10 simultaneous users
- Bulk operations: 100 users creation/deletion
- Service reliability: 99.9% success rate

## Security Testing

### Password Security
- Argon2id hashing validation
- Password strength requirements
- Current password verification

### Input Validation
- SQL injection prevention
- XSS prevention in user inputs
- Email format validation
- Data sanitization

### Authentication
- Invalid credential handling
- Session management (if applicable)
- Authorization checks

## CI/CD Integration

### GitHub Actions Example
```yaml
name: User Routes Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Install dependencies
        run: pip install -r tests/users/requirements.txt
      - name: Run tests
        run: pytest tests/users/ --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Troubleshooting

### Common Issues

1. **Service Not Available**
   ```bash
   # Check service status
   curl http://localhost:7000/docs
   curl http://localhost:8000/docs
   
   # Restart services
   docker-compose restart
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL
   docker-compose logs postgres
   
   # Test connection
   psql postgresql://timele_user:timele_password@localhost:5432/timele_db
   ```

3. **Test Data Conflicts**
   ```bash
   # Clean up test users
   python -c "from tests.utils.db_helpers import cleanup_test_data; cleanup_test_data()"
   ```

4. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :7000
   netstat -tulpn | grep :8000
   ```

### Debug Mode
```bash
# Run tests with detailed output
pytest tests/users/ -v -s --tb=long

# Run single test with debugging
pytest tests/users/db_service/test_users_direct.py::test_create_user_success -v -s
```

## Adding New Tests

### Guidelines
1. **Naming Convention**: `test_<operation>_<scenario>.py`
2. **Documentation**: Include docstrings explaining test purpose
3. **Independence**: Tests should not depend on other tests
4. **Cleanup**: Always clean up created test data
5. **Assertions**: Use descriptive assertion messages

### Template
```python
def test_new_functionality():
    """Test description explaining what this validates"""
    # Arrange
    test_data = create_test_data()
    
    # Act
    response = make_api_call(test_data)
    
    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert_response_structure(response.json())
    
    # Cleanup
    cleanup_test_data(test_data)
```

## Coverage Goals

- **Line Coverage**: > 90%
- **Branch Coverage**: > 85%
- **Function Coverage**: 100%
- **Integration Coverage**: All endpoints tested

## Maintenance

### Regular Tasks
- Update test data as schema evolves
- Review and update performance benchmarks
- Maintain test documentation
- Update dependencies in requirements.txt

### Monitoring
- Track test execution times
- Monitor test failure patterns
- Review coverage reports
- Update test cases for new features

---

For questions or issues with the test suite, please refer to the project documentation or create an issue in the repository.
