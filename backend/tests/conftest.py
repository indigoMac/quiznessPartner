"""
Global test configuration and fixtures for QuizNess backend tests.

This file provides shared fixtures and configuration for all test types:
- Unit tests
- Integration tests
- End-to-end tests
- Performance tests
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING"] = "1"

from db_utils import get_db
from main import app
from models.base import Base
# Import centralized factories
from tests.fixtures.factories import (MockResponses, QuestionFactory,
                                      QuizFactory, QuizResultFactory,
                                      TestDataSets, UserFactory)

# Database configuration for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "isolation_level": None},
    poolclass=StaticPool,
    echo=False,  # Set to True for SQL debugging
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment configuration."""
    # Mock external services during testing
    with patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "test-key",
            "DATABASE_URL": SQLALCHEMY_DATABASE_URL,
            "SECRET_KEY": "test-secret-key-for-testing-only",
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        },
    ):
        yield


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, db_session):
    """Create an authenticated test client with a logged-in user."""
    # Create a test user
    user = UserFactory.create(db_session)
    db_session.commit()

    # Login and get token
    login_data = {
        "username": user.email,
        "password": "testpass123",  # Default password from UserFactory
    }

    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"

    token_data = response.json()
    access_token = token_data["access_token"]

    # Create headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}

    return client, headers


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = UserFactory.create(db_session)
    db_session.commit()
    return user


@pytest.fixture
def sample_quiz(db_session, sample_user):
    """Create a sample quiz with questions for testing."""
    quiz = QuizFactory.create(db_session, user=sample_user)

    # Add questions to the quiz
    _questions = QuestionFactory.create_batch(3, db_session, quiz=quiz)

    db_session.commit()
    return quiz


@pytest.fixture
def sample_quiz_with_results(db_session, sample_user):
    """Create a quiz with submitted results for testing."""
    quiz = QuizFactory.create(db_session, user=sample_user)
    _questions = QuestionFactory.create_batch(5, db_session, quiz=quiz)

    # Create quiz results
    result = QuizResultFactory.create(db_session, user=sample_user, quiz=quiz)

    db_session.commit()
    return quiz, result


@pytest.fixture
def multiple_users_and_quizzes(db_session):
    """Create multiple users with their quizzes for testing."""
    users = UserFactory.create_batch(3, db_session)
    quizzes = []

    for user in users:
        user_quizzes = QuizFactory.create_batch(2, db_session, user=user)
        for quiz in user_quizzes:
            QuestionFactory.create_batch(3, db_session, quiz=quiz)
        quizzes.extend(user_quizzes)

    db_session.commit()
    return users, quizzes


# Mock fixtures for external dependencies
@pytest.fixture
def mock_openai_success():
    """Mock successful OpenAI API response."""
    with patch("openai.ChatCompletion.create") as mock:
        mock.return_value = MockResponses.openai_quiz_generation()
        yield mock


@pytest.fixture
def mock_openai_failure():
    """Mock failed OpenAI API response."""
    with patch("openai.ChatCompletion.create") as mock:
        mock.side_effect = Exception("OpenAI API Error")
        yield mock


@pytest.fixture
def mock_file_upload():
    """Mock file upload for document processing tests."""
    with patch("ai_utils.extract_text_from_pdf") as mock_extract:
        mock_extract.return_value = "Sample document content for quiz generation."
        yield mock_extract


# Performance testing fixtures
@pytest.fixture(scope="session")
def performance_client():
    """Create a client for performance testing that persists across tests."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def load_test_users(db_session):
    """Create multiple users for load testing."""
    users = UserFactory.create_batch(10, db_session)
    db_session.commit()
    return users


# Integration test fixtures
@pytest.fixture
def integration_db_session():
    """Database session specifically for integration tests."""
    # Use a separate test database for integration tests
    integration_engine = create_engine(
        "sqlite:///./integration_test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=integration_engine)
    IntegrationSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=integration_engine
    )

    session = IntegrationSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=integration_engine)


# Data generation fixtures
@pytest.fixture
def educational_quiz_dataset(db_session):
    """Generate educational quiz dataset for testing."""
    return TestDataSets.educational_quiz_set(db_session)


@pytest.fixture
def corporate_quiz_dataset(db_session):
    """Generate corporate training quiz dataset for testing."""
    return TestDataSets.corporate_training_set(db_session)


# E2E test fixtures
@pytest.fixture
def e2e_test_scenario(client, db_session):
    """Set up a complete scenario for E2E testing."""
    # Create test users with different roles
    teacher = UserFactory.create(db_session, email="teacher@test.com")
    students = UserFactory.create_batch(3, db_session)

    # Create quizzes with varying difficulties
    quizzes = []
    for difficulty in ["easy", "medium", "hard"]:
        quiz = QuizFactory.create(
            db_session, user=teacher, difficulty=difficulty, published=True
        )
        QuestionFactory.create_batch(5, db_session, quiz=quiz)
        quizzes.append(quiz)

    db_session.commit()

    return {
        "teacher": teacher,
        "students": students,
        "quizzes": quizzes,
        "client": client,
    }


# Test markers configuration
def pytest_configure(config):
    """Configure custom test markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "auth: marks tests that require authentication")
    config.addinivalue_line("markers", "api: marks tests for API endpoints")
    config.addinivalue_line("markers", "db: marks tests that require database")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Auto-mark tests based on file path
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "/performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


# Cleanup hooks
@pytest.fixture(autouse=True, scope="session")
def cleanup_test_files():
    """Clean up test files after all tests complete."""
    yield

    # Clean up test database files
    test_files = ["test.db", "integration_test.db", "test_coverage.db"]

    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError:
                pass  # Ignore cleanup errors


@pytest.fixture
def auth_headers(authenticated_client):
    """Create authentication headers for performance tests."""
    client, headers = authenticated_client
    return headers
