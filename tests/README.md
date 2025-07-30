# TimeL-E Test Suite

> **Note**: As of January 30, 2025, backend API tests (`tests/users/backend/`) now use **camelCase** field names to match the frontend-facing API standardization. DB service tests continue to use snake_case.

Comprehensive testing framework for the TimeL-E e-commerce platform, covering all services, APIs, and database integrity.

## Quick Start

```bash
# 1. Start all services
docker-compose up -d

# 2. Install test dependencies
pip install -r tests/requirements.txt

# 3. Run all tests
pytest tests/ -v

# 4. Run with coverage
pytest tests/ --cov --cov-report=html
```

## Test Suite Organization

```
tests/
├── README.md                    # This file - main test documentation
├── users/                       # User flow testing (Frontend → Backend /users → DB)
│   ├── backend/                 # Backend /users endpoint tests
│   ├── db_service/              # DB service /users endpoint tests
│   ├── integration/             # End-to-end user workflows
│   ├── utils/                   # User-specific test helpers
│   ├── conftest.py              # User test fixtures
│   ├── requirements.txt         # User test dependencies
│   └── README.md                # User testing documentation
├── database/                    # Database integrity and FK constraint testing
│   ├── test_fk_constraints.py   # Foreign key constraint validation
│   ├── conftest.py              # Database test fixtures
│   ├── requirements.txt         # Database test dependencies
│   └── README.md                # Database testing documentation
└── utils/                       # Shared testing utilities
    ├── fk_helpers.py            # FK-safe test data creation
    └── __init__.py              # Shared utilities documentation
```

## Test Categories

### 1. User Flow Tests (`tests/users/`)
**Purpose**: Test user information flow through the system
**Scope**: Frontend → Backend `/users` endpoints → DB Service → Database

```bash
# Run all user tests
pytest tests/users/ -v

# Run specific user test categories
pytest tests/users/backend/ -v          # Backend API tests
pytest tests/users/db_service/ -v       # DB service tests
pytest tests/users/integration/ -v      # End-to-end workflows
```

### 2. Database Integrity Tests (`tests/database/`)
**Purpose**: Test database constraints and integrity across all tables
**Scope**: FK constraints, schema validation, cross-table relationships

```bash
# Run all database tests
pytest tests/database/ -v

# Run FK constraint tests
pytest tests/database/test_fk_constraints.py -v
```

### 3. Service-Specific Tests (Future)
Additional test directories can be added for other services:
- `tests/products/` - Product management testing
- `tests/orders/` - Order processing testing
- `tests/ml/` - ML service testing

## Prerequisites

### 1. Services Running
Ensure all TimeL-E services are running:

```bash
# Start all services
docker-compose up -d

# Verify services are available
curl http://localhost:8000/docs    # Backend
curl http://localhost:7000/docs    # DB Service
```

### 2. Database Connection
Tests require PostgreSQL access:

```bash
# Test database connection
psql postgresql://timele_user:timele_password@localhost:5432/timele_db
```

### 3. Python Dependencies
Install test dependencies for the test suites you want to run:

```bash
# For user tests
pip install -r tests/users/requirements.txt

# For database tests  
pip install -r tests/database/requirements.txt

# Or install all at once
pip install -r tests/users/requirements.txt -r tests/database/requirements.txt
```

## Running Tests

### All Tests
```bash
# Run entire test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=db_service --cov=backend --cov-report=html

# Run in parallel (faster)
pytest tests/ -n auto
```

or
```bash
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=db_service --cov=backend --cov-report=html

# Run in parallel (faster)
python -m pytest tests/ -n auto
```

### By Test Category
```bash
# User flow tests only
pytest tests/users/ -v

# Database integrity tests only
pytest tests/database/ -v

# Specific test files
pytest tests/users/backend/test_users_api.py -v
pytest tests/database/test_fk_constraints.py -v
```

### By Test Pattern
```bash
# Run tests matching pattern
pytest tests/ -k "user" -v              # All user-related tests
pytest tests/ -k "create" -v            # All creation tests
pytest tests/ -k "login or auth" -v     # Authentication tests
pytest tests/ -k "fk or constraint" -v  # FK constraint tests
```

### By Markers
```bash
# Run tests by markers (if configured)
pytest tests/ -m "integration" -v       # Integration tests only
pytest tests/ -m "slow" -v              # Slow tests only
pytest tests/ -m "not slow" -v          # Skip slow tests
```

### Debug Mode
```bash
# Verbose output with detailed tracebacks
pytest tests/ -v -s --tb=long

# Stop on first failure
pytest tests/ -x

# Run specific test with debugging
pytest tests/users/backend/test_users_api.py::test_user_registration -v -s
```

## Environment Configuration

### Default Configuration
Tests use these default URLs:
```python
DB_SERVICE_URL = "http://localhost:7000"
BACKEND_URL = "http://localhost:8000"  
POSTGRES_URL = "postgresql://timele_user:timele_password@localhost:5432/timele_db"
```

### Override with Environment Variables
```bash
# Set custom test URLs
export TEST_DB_SERVICE_URL="http://localhost:7000"
export TEST_BACKEND_URL="http://localhost:8000"
export TEST_POSTGRES_URL="postgresql://timele_user:timele_password@localhost:5432/timele_db"

# Run tests with custom configuration
pytest tests/ -v
```

## Test Data Management

### Isolation Strategy
- Each test creates unique test data using timestamps
- Tests clean up their own data automatically
- Tests are independent and can run in any order
- No shared state between tests

### Database State
- Tests use the same PostgreSQL instance as development
- Test data is clearly identifiable (contains timestamps/test markers)
- Automatic cleanup prevents data pollution
- FK-safe creation and cleanup order

### Example Test Data
```python
# User test data
test_user_1673123456@timele-test.com

# Product test data  
Test Product 1673123456

# Order test data
Order #1673123456
```

## Performance and Load Testing

### Response Time Targets
- User creation: < 500ms
- User login: < 200ms
- Profile retrieval: < 100ms
- Database operations: < 100ms

### Load Testing
```bash
# Run performance benchmarks
pytest tests/ --benchmark-only

# Concurrent test execution
pytest tests/ -n 4  # 4 parallel workers
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: TimeL-E Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: timele_password
          POSTGRES_USER: timele_user
          POSTGRES_DB: timele_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Start services
        run: docker-compose up -d
        
      - name: Wait for services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8000/docs; do sleep 2; done'
          timeout 60 bash -c 'until curl -f http://localhost:7000/docs; do sleep 2; done'
      
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      
      - name: Run tests
        run: pytest tests/ --cov --cov-report=xml -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/ -x
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

#### 1. Services Not Available
```bash
# Check service status
docker-compose ps

# Check service logs
docker-compose logs backend
docker-compose logs db_service
docker-compose logs postgres

# Restart services
docker-compose restart
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Test direct connection
psql postgresql://timele_user:timele_password@localhost:5432/timele_db

# Reset database if needed
docker-compose down
docker-compose up -d
```

#### 3. Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :7000
netstat -tulpn | grep :5432

# Kill processes if needed
sudo lsof -ti:8000 | xargs kill -9
```

#### 4. Test Data Conflicts
```bash
# Clean up test data manually
python -c "
from tests.utils.fk_helpers import FKTestDataManager
import psycopg2
conn = psycopg2.connect('postgresql://timele_user:timele_password@localhost:5432/timele_db')
manager = FKTestDataManager(conn)
manager.cleanup_all()
"
```

#### 5. Import Errors
```bash
# Ensure you're in the project root
cd /path/to/TimeL-E

# Install missing dependencies
pip install -r tests/users/requirements.txt
pip install -r tests/database/requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Debug Specific Issues

#### Test Failures
```bash
# Run with maximum verbosity
pytest tests/path/to/failing_test.py -vvv -s --tb=long

# Run single test with debugging
pytest tests/users/backend/test_users_api.py::test_specific_function -vvv -s

# Use pytest debugger
pytest tests/path/to/test.py --pdb
```

#### Performance Issues
```bash
# Profile test execution
pytest tests/ --durations=10

# Run tests with timing
pytest tests/ -v --tb=short --durations=0
```

#### Coverage Issues
```bash
# Generate detailed coverage report
pytest tests/ --cov --cov-report=html --cov-report=term-missing

# View coverage report
open htmlcov/index.html
```

## Adding New Tests

### Guidelines
1. **Choose the right directory**:
   - User flow tests → `tests/users/`
   - Database integrity → `tests/database/`
   - Service-specific → create new directory

2. **Follow naming conventions**:
   - Files: `test_<feature>_<scenario>.py`
   - Functions: `test_<operation>_<expected_result>`
   - Classes: `Test<Feature><Scenario>`

3. **Use appropriate fixtures**:
   - User tests: Use fixtures from `tests/users/conftest.py`
   - Database tests: Use fixtures from `tests/database/conftest.py`
   - Shared utilities: Import from `tests/utils/`

4. **Ensure cleanup**:
   - Always clean up test data
   - Use context managers when possible
   - Follow FK-safe cleanup order

### Example Test Structure
```python
def test_new_feature_success(db_connection, test_user_data):
    """Test that new feature works correctly with valid data"""
    # Arrange
    user_id = create_test_user(test_user_data)
    
    # Act
    response = call_api_endpoint(user_id)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Cleanup (if not using fixtures)
    cleanup_test_user(user_id)
```

## Coverage Goals

- **Line Coverage**: > 90%
- **Branch Coverage**: > 85%
- **Function Coverage**: 100%
- **Integration Coverage**: All critical user flows tested

## Maintenance

### Regular Tasks
- Update test dependencies monthly
- Review and update performance benchmarks
- Clean up obsolete test data patterns
- Update documentation for new features

### Monitoring
- Track test execution times in CI
- Monitor test failure patterns
- Review coverage reports weekly
- Update test cases for new features

---

## Quick Reference

### Most Common Commands
```bash
# Start everything and run all tests
docker-compose up -d && pytest tests/ -v

# Run user tests only
pytest tests/users/ -v

# Run database tests only  
pytest tests/database/ -v

# Run with coverage
pytest tests/ --cov --cov-report=html

# Debug failing test
pytest tests/path/to/test.py::test_function -vvv -s
```

### Key Files
- `tests/users/conftest.py` - User test fixtures
- `tests/database/conftest.py` - Database test fixtures  
- `tests/utils/fk_helpers.py` - FK-safe test utilities
- `docker-compose.yml` - Service configuration

For detailed information about specific test suites, see:
- [User Tests Documentation](users/README.md)
- [Database Tests Documentation](database/README.md)
