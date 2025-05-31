# Testing Guide for QuizNess Backend

This guide covers the comprehensive testing environment setup for the QuizNess backend application.

## Overview

Our testing infrastructure includes:

- **Unit Tests**: Fast, isolated tests for individual functions
- **Integration Tests**: End-to-end API workflow tests
- **Performance Tests**: Load and response time testing
- **Security Tests**: Vulnerability scanning
- **CI/CD Pipeline**: Automated testing on every commit

## Quick Start

### Local Development Testing

```bash
# Install development dependencies
cd backend
pip install -r requirements-dev.txt

# Run all tests (except slow performance tests)
./scripts/test_local.sh

# Run specific test types
./scripts/test_local.sh --type unit
./scripts/test_local.sh --type integration
./scripts/test_local.sh --type performance
```

### Load Testing

```bash
# Quick load test with default settings
./scripts/load_test.sh

# Custom load test
./scripts/load_test.sh --users 50 --spawn-rate 5 --run-time 10m --headless

# Load test with Docker
./scripts/load_test.sh --docker
```

## Test Environment Setup

### 1. Database Configuration

The testing environment supports both SQLite (for quick local tests) and PostgreSQL (for integration tests):

**SQLite (Default for Unit Tests):**

```bash
export TEST_DATABASE_URL="sqlite:///./test.db"
```

**PostgreSQL (For Integration Tests):**

```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5434/quizness_test"
```

### 2. Environment Variables

Key environment variables for testing:

```bash
export ENVIRONMENT="test"
export SECRET_KEY="test-secret-key-for-testing"
export OPENAI_API_KEY="test-openai-key"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
```

## Test Types and Organization

### Unit Tests

**Location**: `tests/test_*.py` with `@pytest.mark.unit`
**Purpose**: Test individual functions and classes in isolation
**Database**: SQLite in-memory or file-based
**Execution Time**: < 1 second per test

```bash
# Run only unit tests
pytest tests/ -m "unit"
```

### Integration Tests

**Location**: `tests/test_integration.py`
**Purpose**: Test complete API workflows and database interactions
**Database**: PostgreSQL test database
**Execution Time**: 1-10 seconds per test

```bash
# Run only integration tests
pytest tests/ -m "integration"
```

### Performance Tests

**Location**: `tests/test_performance.py`
**Purpose**: Measure response times and system performance under load
**Markers**: `@pytest.mark.slow`

```bash
# Run performance tests
pytest tests/ -m "slow"
```

## Test Data Management

### Factories

We use `factory_boy` for creating test data:

```python
# Create a test user
user = UserFactory()

# Create a quiz with questions
quiz = QuizFactory(user=user)
questions = QuestionFactory.create_batch(5, quiz=quiz)
```

### Fixtures

Common fixtures available in all tests:

- `db_session`: Fresh database session for each test
- `client`: FastAPI test client
- `test_user`: Pre-created test user
- `test_quiz`: Pre-created test quiz
- `auth_headers`: Authentication headers for requests

## Coverage Reporting

### Local Coverage

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# Open coverage report (macOS)
open htmlcov/index.html
```

### Coverage Configuration

Coverage settings are defined in `.coveragerc`:

- Excludes test files, migrations, and utility scripts
- Targets 80% coverage minimum
- Generates HTML, XML, and terminal reports

## Docker Testing

### Test Environment

```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up backend-test

# Run specific test type
docker-compose -f docker-compose.test.yml run backend-test pytest tests/ -m "unit"
```

### Load Testing with Docker

```bash
# Start Locust web interface
docker-compose -f docker-compose.test.yml up locust-test

# Access at http://localhost:8089
```

## CI/CD Testing

### GitHub Actions Pipeline

Our CI/CD pipeline includes:

1. **Matrix Testing**: Tests across Python 3.9, 3.10, 3.11
2. **Parallel Execution**: Unit and integration tests run separately
3. **Security Scanning**: Safety, Bandit, and Semgrep checks
4. **Performance Testing**: Runs on main branch pushes
5. **Docker Testing**: Validates containerized builds

### Test Stages

1. **Lint and Format**: Code quality checks
2. **Unit Tests**: Fast, isolated tests
3. **Integration Tests**: API workflow tests
4. **Security Scan**: Vulnerability detection
5. **Performance Tests**: Load and response time validation
6. **Docker Build**: Container validation

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import patch

@pytest.mark.unit
def test_generate_quiz_from_text():
    with patch('ai_utils.openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = mock_openai_response

        result = generate_quiz_from_text("Test content", "Science", 5)

        assert len(result) == 5
        assert all("question" in q for q in result)
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_complete_quiz_workflow(client, auth_headers, db_session):
    # Create quiz
    response = client.post(
        "/api/v1/generate-quiz",
        headers=auth_headers,
        json={"content": "Test", "topic": "Science", "num_questions": 3}
    )

    assert response.status_code == 200
    quiz_id = response.json()["id"]

    # Verify in database
    quiz = db_session.query(Quiz).filter(Quiz.id == quiz_id).first()
    assert quiz is not None
```

## Performance Testing

### Response Time Benchmarks

- Health check: < 100ms average
- Quiz generation: < 2s average
- Quiz retrieval: < 500ms average
- Answer submission: < 1s average

### Load Testing Scenarios

1. **Light Load**: 10 users, 2/sec spawn rate
2. **Normal Load**: 50 users, 5/sec spawn rate
3. **Heavy Load**: 100 users, 10/sec spawn rate
4. **Stress Test**: 200+ users, 20/sec spawn rate

### Locust Test Scenarios

- **90% Read Operations**: Health checks, quiz retrieval
- **8% Write Operations**: Quiz creation, answer submission
- **2% File Operations**: Document upload

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:

   ```bash
   # Ensure test database is running
   docker-compose -f docker-compose.test.yml up -d db-test
   ```

2. **Import Errors**:

   ```bash
   # Ensure you're in the backend directory
   cd backend
   export PYTHONPATH="."
   ```

3. **Permission Errors**:
   ```bash
   # Make scripts executable
   chmod +x scripts/test_local.sh
   chmod +x scripts/load_test.sh
   ```

### Debug Mode

Run tests with verbose output and debug information:

```bash
pytest tests/ -v -s --tb=long --durations=10
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Test names should describe what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Services**: Don't rely on external APIs in tests
5. **Use Factories**: Generate test data consistently
6. **Measure Performance**: Include timing assertions where relevant
7. **Test Edge Cases**: Include error conditions and boundary values

## Continuous Integration

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pip install pre-commit
pre-commit install
```

### Code Quality Gates

All code must pass:

- Black formatting
- isort import sorting
- flake8 linting
- mypy type checking
- 80% test coverage
- Security scans

## Deployment Testing

### Staging Environment

Tests run automatically on `develop` branch:

- Full test suite
- Performance validation
- Security scanning
- Container testing

### Production Environment

Tests run on `main` branch with additional:

- Extended performance tests
- Load testing validation
- Security verification
- Deployment smoke tests

## Metrics and Monitoring

### Test Metrics

- **Coverage**: Target 80% minimum
- **Performance**: Response time percentiles
- **Reliability**: Test success rates
- **Security**: Vulnerability scan results

### Monitoring

- Codecov for coverage tracking
- GitHub Actions for CI/CD status
- Performance benchmarks in CI logs
- Security scan reports in artifacts
