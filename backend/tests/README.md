# QuizNess Backend Testing Suite

A comprehensive, professional testing framework following industry best practices.

## 🏗️ **Testing Architecture**

### **Test Categories**

```
tests/
├── unit/              # ⚡ Fast isolated tests (< 100ms each)
│   ├── test_models.py     # Model validation & business logic
│   ├── test_auth.py       # Authentication utilities
│   ├── test_utils.py      # Utility functions
│   └── test_services.py   # Service layer logic
├── integration/       # 🔗 Component interaction tests
│   ├── test_api.py        # API endpoint integration
│   ├── test_database.py   # Database operations
│   └── test_auth_flow.py  # Authentication flows
├── e2e/              # 🌐 End-to-end user journeys
│   ├── test_quiz_flow.py  # Complete quiz creation/taking
│   ├── test_user_flow.py  # User registration/login
│   └── test_admin_flow.py # Admin operations
├── performance/      # 🚀 Load & performance tests
│   ├── test_load.py       # Load testing
│   └── test_stress.py     # Stress testing
└── fixtures/         # 📦 Shared test data & utilities
    ├── factories.py       # Data factories
    ├── mocks.py          # Mock objects
    └── helpers.py        # Test utilities
```

## 🎯 **Testing Strategy**

### **Test Pyramid**

- **Unit Tests (70%)**: Fast, isolated, comprehensive
- **Integration Tests (20%)**: Component interactions
- **E2E Tests (10%)**: Full user journeys

### **Coverage Goals**

- **Overall**: 90%+ coverage
- **Critical paths**: 100% coverage
- **New features**: 95%+ coverage requirement

## 🧪 **Test Types**

### **Unit Tests** ⚡

```bash
# Run all unit tests (fast)
make test-unit
python3 -m pytest tests/unit/ -v
```

- Test individual functions/classes in isolation
- Mock external dependencies
- Focus on business logic validation
- Should run in < 5 seconds total

### **Integration Tests** 🔗

```bash
# Run integration tests
make test-integration
python3 -m pytest tests/integration/ -v
```

- Test component interactions
- Use real database (test instance)
- Test API contracts
- Should run in < 30 seconds total

### **E2E Tests** 🌐

```bash
# Run end-to-end tests
make test-e2e
python3 -m pytest tests/e2e/ -v
```

- Test complete user workflows
- Use realistic test data
- Test UI → API → Database flows
- Can be slower (1-2 minutes)

### **Performance Tests** 🚀

```bash
# Run performance tests
make test-performance
python3 -m pytest tests/performance/ -v
```

- Load testing with Locust
- Stress testing
- Response time validation
- Memory usage monitoring

## 🛠️ **Test Tools & Libraries**

### **Core Testing**

- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `pytest-xdist`: Parallel execution
- `factory-boy`: Test data generation
- `faker`: Realistic fake data

### **Mocking & Stubbing**

- `unittest.mock`: Python mocking
- `pytest-mock`: Pytest integration
- `responses`: HTTP mocking
- `freezegun`: Time mocking

### **Performance**

- `locust`: Load testing
- `pytest-benchmark`: Performance regression

## 📊 **Coverage & Quality**

### **Coverage Requirements**

```bash
# Generate coverage report
make test-coverage
open backend/htmlcov/index.html
```

### **Quality Gates**

- All tests must pass
- 90%+ code coverage
- No critical security issues
- Performance benchmarks met

## 🚀 **Best Practices**

### **Test Naming**

```python
def test_should_create_quiz_when_valid_data_provided():
    """Tests should describe behavior, not implementation"""
    pass
```

### **Test Structure (AAA Pattern)**

```python
def test_user_creation():
    # Arrange
    user_data = {"email": "test@example.com"}

    # Act
    user = create_user(user_data)

    # Assert
    assert user.email == "test@example.com"
```

### **Test Independence**

- Each test should be independent
- Use fixtures for setup/teardown
- No shared state between tests
- Clean database state per test

### **Error Testing**

```python
def test_should_raise_error_when_invalid_email():
    with pytest.raises(ValidationError):
        create_user({"email": "invalid-email"})
```

## 🏃‍♂️ **Running Tests**

### **Quick Commands**

```bash
# All tests (CI pipeline)
make test

# Development workflow
make test-unit          # Fast feedback loop
make test-integration   # Before committing
make test-e2e          # Before releasing

# Coverage and quality
make test-coverage     # Generate reports
make lint             # Code quality
make pre-commit       # Pre-commit hooks
```

### **Advanced Options**

```bash
# Run specific test file
pytest tests/unit/test_models.py -v

# Run tests with specific marker
pytest -m "not slow" -v

# Run tests in parallel
pytest tests/ -n auto

# Debug failing test
pytest tests/unit/test_models.py::test_user_creation -vvs --pdb
```

## 🔧 **Development Workflow**

### **TDD Process**

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code quality

### **Feature Development**

1. Write unit tests for new functionality
2. Implement feature
3. Add integration tests
4. Add E2E tests for user-facing features
5. Ensure coverage targets met

### **Bug Fixes**

1. Write test that reproduces bug
2. Fix the bug
3. Verify test passes
4. Check regression coverage

## 📈 **Continuous Integration**

### **CI Pipeline Stages**

```yaml
1. Lint & Format Check
2. Unit Tests (parallel)
3. Integration Tests
4. Security Scanning
5. Performance Tests
6. Coverage Report
7. Deploy (if all pass)
```

## 🎯 **Test Markers**

```python
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.slow         # Long-running tests
@pytest.mark.auth         # Authentication tests
@pytest.mark.api          # API endpoint tests
@pytest.mark.db           # Database tests
@pytest.mark.security     # Security tests
```

## 📚 **Resources**

- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Guide](https://factoryboy.readthedocs.io/)
- [Testing Best Practices](https://testing.googleblog.com/)
- [Test Pyramid Pattern](https://martinfowler.com/articles/practical-test-pyramid.html)
