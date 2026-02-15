# StudyPulse Testing Infrastructure

Production-ready testing suite for StudyPulse backend with comprehensive coverage.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_security.py     # Password hashing, JWT tokens
│   ├── test_rag_validator.py # Question quality validation
│   └── test_cache.py        # Cache system tests
├── integration/             # API integration tests
│   ├── test_auth_api.py     # Authentication endpoints
│   ├── test_study_api.py    # Study session endpoints
│   └── test_mock_test_api.py # Mock test endpoints
├── e2e/                     # End-to-end tests
│   └── test_complete_user_journey.py # Full user workflows
└── load/                    # Performance & load tests
    └── test_concurrent_users.py # Concurrent user scenarios
```

## Quick Start

### Install Dependencies

```bash
cd studypulse/backend
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v -m e2e

# Load tests (slow, use sparingly)
pytest tests/load -v -m load
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Run Specific Tests

```bash
# Single test file
pytest tests/unit/test_security.py -v

# Single test class
pytest tests/unit/test_security.py::TestPasswordHashing -v

# Single test method
pytest tests/unit/test_security.py::TestPasswordHashing::test_password_hashing -v

# Tests matching pattern
pytest -k "test_login" -v
```

## Test Markers

Tests are organized with markers for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only E2E tests
pytest -m e2e

# Run quick smoke tests
pytest -m smoke

# Skip slow tests
pytest -m "not slow"

# Skip load tests
pytest -m "not load"
```

## Coverage Requirements

- Minimum coverage: **70%**
- Target coverage: **80%+**
- Critical paths: **90%+**

## Writing Tests

### Unit Test Example

```python
import pytest
from app.core.security import get_password_hash, verify_password

def test_password_hashing():
    """Test password is hashed correctly."""
    password = "SecurePassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
```

### Integration Test Example

```python
import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_user_registration(test_client):
    """Test user registration endpoint."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123!"
    }

    response = test_client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == user_data["email"]
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_with_authenticated_user(test_client, test_user, auth_headers):
    """Test using authenticated user fixture."""
    response = test_client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == test_user.email
```

## Available Fixtures

### Database Fixtures
- `test_db` - Fresh in-memory database for each test
- `test_exam` - Pre-created exam
- `test_topic` - Pre-created topic
- `test_questions` - List of test questions

### User Fixtures
- `test_user` - Regular test user
- `admin_user` - Admin user
- `test_user_token` - JWT token for test user
- `auth_headers` - Authorization headers
- `admin_headers` - Admin authorization headers

### Mock Fixtures
- `mock_ollama` - Mocked LLM client
- `mock_vector_store` - Mocked vector database
- `mock_cache` - Mocked Redis cache

### Utility Fixtures
- `test_client` - FastAPI test client
- `sample_question_data` - Valid question data
- `invalid_question_data` - Invalid question data
- `performance_tracker` - Track performance metrics

## Continuous Integration

Tests run automatically on:

- **Every push** to main/master
- **Every pull request**

### CI Workflow

1. **Code Quality** - Linting, formatting, security scans
2. **Unit Tests** - Fast, isolated tests
3. **Integration Tests** - API endpoint tests
4. **E2E Tests** - Complete user journeys
5. **Coverage Report** - Uploaded to Codecov

### Coverage Reports

- HTML report: Downloadable artifact in GitHub Actions
- XML report: Uploaded to Codecov
- PR Comments: Automatic coverage comments on pull requests

## Best Practices

### DO

- ✅ Write tests for every new feature
- ✅ Use appropriate test markers
- ✅ Mock external dependencies (Ollama, Redis)
- ✅ Test both success and failure cases
- ✅ Keep tests fast (< 1 second each)
- ✅ Use descriptive test names
- ✅ Test edge cases and boundary conditions

### DON'T

- ❌ Commit code without tests
- ❌ Skip tests in CI
- ❌ Test implementation details
- ❌ Write flaky tests
- ❌ Share state between tests
- ❌ Ignore test failures

## Debugging Tests

### Run with verbose output

```bash
pytest -vv --tb=long
```

### Run with print statements

```bash
pytest -s
```

### Run single test with debugging

```bash
pytest tests/unit/test_security.py::test_password_hashing -vv -s
```

### Use pytest debugger

```python
import pytest

def test_something():
    value = compute_value()
    pytest.set_trace()  # Debugger breakpoint
    assert value == expected
```

## Performance Testing

### Run Load Tests

```bash
# Warning: These tests are slow
pytest tests/load -v -m load

# Run specific load test
pytest tests/load/test_concurrent_users.py::TestConcurrentUsers::test_100_concurrent_users -v
```

### Load Test Scenarios

- **100 concurrent users** - Standard load
- **Burst traffic** - Sudden spike in requests
- **Sustained load** - Long-running stress test
- **Database performance** - Concurrent reads/writes

## Troubleshooting

### Tests fail locally but pass in CI

- Check Python version (CI uses 3.10)
- Check environment variables
- Clear `.pytest_cache/` and `__pycache__/`

### Import errors

```bash
# Ensure you're in the backend directory
cd studypulse/backend
pytest
```

### Database errors

- Tests use in-memory SQLite
- Each test gets a fresh database
- Check fixture dependencies

### Async errors

- Use `@pytest.mark.asyncio` for async tests
- Ensure `pytest-asyncio` is installed
- Check `asyncio_mode = auto` in pytest.ini

## Migration from Old Test Scripts

Old test scripts in `backend/` directory:
- `test_*.py` - Move to appropriate test category
- `check_*.py` - Convert to unit tests or integration tests
- `verify_*.py` - Convert to E2E tests
- `seed_*.py` - Use as test fixtures or data factories

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Support

For questions or issues with tests:
1. Check existing test examples
2. Review fixture documentation in `conftest.py`
3. Review this README
4. Ask the team
