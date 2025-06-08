# FastAPI Task Management - Testing Guide

## 🧪 Testing Strategy

This project follows a comprehensive testing approach with multiple layers to ensure code quality, reliability, and performance.

### Testing Pyramid

```
    🔺 E2E Tests (Few)
      - Complete user workflows
      - API integration tests
      - Real-world scenarios

  🔹 Integration Tests (Some)
    - Database operations
    - Service layer integration
    - Feature interactions

🔷 Unit Tests (Many)
  - Business logic
  - Security functions
  - Schema validation
  - Repository operations
```

## 📁 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (isolated components)
│   └── test_auth.py              # Authentication unit tests
├── integration/                   # Integration tests (with database)
│   └── test_auth_integration.py  # Auth database integration
├── e2e/                          # End-to-end tests (full API flows)
│   └── test_api_flows.py         # Complete user workflows
├── utils/                        # Test utilities
│   └── performance.py           # Performance testing tools
└── test_performance.py          # Performance and load tests
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install project with dev dependencies
pip install -e ".[dev]"

# Or install dev dependencies separately
pip install pytest pytest-asyncio pytest-cov httpx aiosqlite
```

### 2. Run Tests

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test types
python scripts/run_tests.py unit
python scripts/run_tests.py integration
python scripts/run_tests.py e2e
python scripts/run_tests.py performance

# Run with coverage
python scripts/run_tests.py coverage

# Run fast tests (exclude slow performance tests)
python scripts/run_tests.py fast

# Run with linting
python scripts/run_tests.py unit --with-lint
```

### 3. Direct pytest Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test class
pytest tests/unit/test_auth.py::TestSecurity

# Run specific test method
pytest tests/unit/test_auth.py::TestSecurity::test_password_hashing

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s

# Run tests matching pattern
pytest -k "test_auth"

# Run tests with specific markers
pytest -m "not slow"  # Skip slow tests
pytest -m "performance"  # Only performance tests
```

## 🔧 Test Configuration

### pytest.ini Options

Our `pyproject.toml` includes:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
```

### Test Markers

- `@pytest.mark.slow` - Long-running tests (load tests)
- `@pytest.mark.performance` - Performance benchmark tests
- `@pytest.mark.asyncio` - Async tests (auto-applied by pytest-asyncio)

## 📋 Test Types Explained

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Characteristics**:

- Fast execution (< 1 second each)
- No external dependencies
- Mocked database and external services
- High code coverage target (90%+)

**Example**:

```python
def test_password_hashing():
    password = "TestPassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions with real dependencies

**Characteristics**:

- Real database operations (SQLite for speed)
- Tests data persistence and retrieval
- Validates business logic with dependencies
- Medium execution time

**Example**:

```python
async def test_user_repository_crud_operations(db_session: AsyncSession):
    repo = UserRepository(db_session)

    # Create user
    user_data = UserCreate(...)
    created_user = await repo.create_user(user_data)

    # Verify in database
    found_user = await repo.get_by_email(user_data.email)
    assert found_user.id == created_user.id
```

### 3. E2E Tests (`tests/e2e/`)

**Purpose**: Test complete user workflows through the API

**Characteristics**:

- Full HTTP requests to real API endpoints
- Tests complete user journeys
- Validates API contracts and responses
- Realistic data validation

**Example**:

```python
def test_complete_user_flow(test_client: TestClient):
    # Register user
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    # Login
    response = test_client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]

    # Access protected route
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
```

### 4. Performance Tests (`tests/test_performance.py`)

**Purpose**: Measure and validate API performance

**Characteristics**:

- Response time benchmarks
- Throughput measurements
- Load testing under concurrent users
- Performance regression prevention

**Metrics Tracked**:

- Average response time
- 95th/99th percentile response times
- Requests per second
- Success rate under load
- Memory and CPU usage

## 🛠️ Test Fixtures and Utilities

### Key Fixtures (conftest.py)

```python
@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Fresh database session for each test"""

@pytest.fixture
def test_client(override_get_db) -> TestClient:
    """Test client with database override"""

@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """Async test client for concurrent testing"""

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Pre-created test user"""

@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Authorization headers with valid JWT token"""
```

### Performance Testing Utilities

```python
from tests.utils.performance import PerformanceBenchmark, LoadTestScenarios

# Measure endpoint performance
stats = PerformanceBenchmark.measure_endpoint_performance(
    client=test_client,
    method="POST",
    url="/api/v1/auth/login",
    iterations=100,
    json=login_data
)

# Run load tests
results = await LoadTestScenarios.registration_load_test(
    client=async_client,
    concurrent_users=50,
    registrations_per_user=5
)
```

## 📊 Coverage and Quality Metrics

### Coverage Targets

- **Overall**: 80%+ code coverage
- **Unit Tests**: 90%+ coverage for business logic
- **Integration Tests**: 100% coverage for critical paths
- **E2E Tests**: 100% coverage for user workflows

### Quality Gates

```bash
# Coverage threshold (fails if below 80%)
pytest --cov=app --cov-fail-under=80

# Performance thresholds
- Health endpoints: < 10ms average
- Login endpoint: < 500ms average
- Registration: < 2s maximum
- Protected routes: 95th percentile < 200ms

# Code quality
ruff check app/ tests/     # Linting
black --check app/ tests/  # Formatting
mypy app/                  # Type checking
```

## 🎯 Writing Good Tests

### Unit Test Best Practices

```python
class TestUserService:
    """Group related tests in classes"""

    async def test_register_user_success(self, auth_service, user_create_data):
        """Test names should describe what's being tested"""
        # Arrange
        with patch.object(auth_service.user_repo, 'email_exists', return_value=False):

            # Act
            result = await auth_service.register_user(user_create_data)

            # Assert
            assert result.message == "User registered successfully"
            assert result.user.email == user_create_data.email

    async def test_register_user_email_exists(self, auth_service, user_create_data):
        """Test error cases explicitly"""
        with patch.object(auth_service.user_repo, 'email_exists', return_value=True):

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(user_create_data)

            assert exc_info.value.status_code == 400
            assert "Email already registered" in str(exc_info.value.detail)
```

### Integration Test Best Practices

```python
async def test_auth_service_registration_flow(db_session: AsyncSession):
    """Test complete service flow with real database"""
    service = AuthService(db_session)

    user_data = UserCreate(
        email="service@example.com",
        username="serviceuser",
        full_name="Service Test User",
        password="ServicePass123"
    )

    # Test the complete flow
    result = await service.register_user(user_data)

    # Verify result
    assert result.message == "User registered successfully"

    # Verify database state
    repo = UserRepository(db_session)
    db_user = await repo.get_by_email(user_data.email)
    assert db_user is not None
    assert db_user.email == user_data.email
```

### E2E Test Best Practices

```python
def test_user_registration_success(test_client: TestClient):
    """Test API endpoint with realistic data"""
    user_data = {
        "email": "e2e@example.com",
        "username": "e2euser",
        "full_name": "E2E Test User",
        "password": "E2EPassword123"
    }

    response = test_client.post("/api/v1/auth/register", json=user_data)

    # Test HTTP status
    assert response.status_code == 201

    # Test response structure
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert data["user"]["email"] == user_data["email"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

## 🚨 Debugging Test Failures

### Common Issues and Solutions

**1. Database State Issues**

```bash
# Clean test database
rm test.db

# Check for test isolation
pytest tests/integration/ -v --tb=long
```

**2. Async Test Issues**

```python
# Ensure proper async fixtures
@pytest_asyncio.fixture
async def async_fixture():
    # Setup
    yield value
    # Cleanup
```

**3. Performance Test Failures**

```bash
# Run with more verbose output
pytest tests/test_performance.py -v -s

# Check system resources
htop  # Monitor CPU/memory during tests
```

**4. JWT Token Issues**

```python
# Check token expiration in tests
token = create_access_token(data={"sub": "testuser"})
print(f"Token: {token}")

# Verify token in test
decoded = verify_token(token)
assert decoded == "testuser"
```

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run linting
        run: python scripts/run_tests.py lint

      - name: Run unit tests
        run: python scripts/run_tests.py unit

      - name: Run integration tests
        run: python scripts/run_tests.py integration

      - name: Run E2E tests
        run: python scripts/run_tests.py e2e

      - name: Generate coverage report
        run: python scripts/run_tests.py coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

## 🔄 Test Development Workflow

1. **Write failing test first** (TDD approach)
2. **Make test pass** with minimal code
3. **Refactor** while keeping tests green
4. **Add integration tests** for component interactions
5. **Add E2E tests** for critical user workflows
6. **Add performance tests** for important endpoints
7. **Verify coverage** meets targets

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [HTTPx Testing](https://www.python-httpx.org/advanced/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
