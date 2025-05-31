import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock, ANY
import io
import json
from auth.auth_utils import get_password_hash

from main import app
from db_utils import get_db
from models.base import Base
from models.quiz import Quiz
from models.question import Question
from models.result import Result
from models.user import User

# Create a test database in memory
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
Base.metadata.reflect = lambda *args, **kwargs: None

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables after the test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_token(setup_db):
    # Create a test user
    db = TestingSessionLocal()
    hashed_password = get_password_hash("testpassword")
    test_user = User(email="test@example.com", hashed_password=hashed_password)
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Get auth token
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch('main.generate_quiz_from_text')
@patch('main.create_quiz')
@patch('main.add_questions_to_quiz')
def test_generate_quiz(mock_add_questions, mock_create_quiz, mock_generate_quiz, auth_token):
    # Mock the quiz generation
    mock_questions = [
        {
            "question": "What is the capital of France?",
            "options": ["Berlin", "Paris", "London", "Madrid"],
            "correct_answer": 1
        }
    ]
    mock_generate_quiz.return_value = mock_questions
    
    # Mock the database operations
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    mock_create_quiz.return_value = mock_quiz
    
    # Test the endpoint with auth token
    response = client.post(
        "/api/v1/generate-quiz",
        headers=auth_token,
        json={"content": "Test content", "topic": "Geography", "num_questions": 1}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == "1"
    assert "questions" in data
    assert len(data["questions"]) == 1
    assert data["topic"] == "Geography"
    
    # Verify the mocks were called correctly
    mock_generate_quiz.assert_called_once_with("Test content", "Geography", 1)
    mock_create_quiz.assert_called_once()
    mock_add_questions.assert_called_once_with(ANY, 1, mock_questions)

@patch('main.generate_quiz_from_text')
def test_generate_quiz_error(mock_generate_quiz, auth_token):
    # Mock the quiz generation to raise an exception
    mock_generate_quiz.side_effect = Exception("Failed to generate quiz")
    
    # Test the endpoint with auth token
    response = client.post(
        "/api/v1/generate-quiz",
        headers=auth_token,
        json={"content": "Test content", "topic": "Geography", "num_questions": 1}
    )
    
    # Verify the response
    assert response.status_code == 500
    assert "Error generating quiz" in response.json()["detail"]

def test_generate_quiz_invalid_input(auth_token):
    # Test with missing required field
    response = client.post(
        "/api/v1/generate-quiz",
        headers=auth_token,
        json={"topic": "Geography", "num_questions": 1}  # Missing 'content'
    )
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

@patch('main.extract_text_from_pdf')
@patch('main.generate_quiz_from_text')
@patch('main.create_quiz')
@patch('main.add_questions_to_quiz')
def test_upload_document(mock_add_questions, mock_create_quiz, mock_generate_quiz, mock_extract_text, auth_token):
    # Mock the text extraction and quiz generation
    mock_extract_text.return_value = "Extracted text from PDF"
    mock_questions = [
        {
            "question": "What is the capital of France?",
            "options": ["Berlin", "Paris", "London", "Madrid"],
            "correct_answer": 1
        }
    ]
    mock_generate_quiz.return_value = mock_questions
    
    # Mock the database operations
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    mock_create_quiz.return_value = mock_quiz
    
    # Create a mock PDF file
    pdf_content = io.BytesIO(b"%PDF-1.5 mock pdf content")
    
    # Test the endpoint with auth token
    response = client.post(
        "/api/v1/upload-document",
        headers=auth_token,
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"topic": "Geography", "num_questions": "3"}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == "1"
    assert "questions" in data
    assert len(data["questions"]) == 1
    assert data["topic"] == "Geography"
    
    # Verify the mocks were called correctly
    mock_extract_text.assert_called_once()
    mock_generate_quiz.assert_called_once_with("Extracted text from PDF", "Geography", 3)
    mock_create_quiz.assert_called_once()
    mock_add_questions.assert_called_once()

@patch('main.extract_text_from_pdf')
def test_upload_document_extraction_error(mock_extract_text, auth_token):
    # Mock the text extraction to raise an exception
    mock_extract_text.side_effect = Exception("Failed to extract text")
    
    # Create a mock PDF file
    pdf_content = io.BytesIO(b"%PDF-1.5 mock pdf content")
    
    # Test the endpoint with auth token
    response = client.post(
        "/api/v1/upload-document",
        headers=auth_token,
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"topic": "Geography", "num_questions": "3"}
    )
    
    # Verify the response
    assert response.status_code == 500
    assert "Error processing document" in response.json()["detail"]

def test_upload_document_no_file(auth_token):
    # Test without uploading a file
    response = client.post(
        "/api/v1/upload-document",
        headers=auth_token,
        files={},  # No file
        data={"topic": "Geography", "num_questions": "3"}
    )
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

@patch('main.get_quiz_with_questions')
def test_get_quiz(mock_get_quiz, auth_token):
    # Mock the database query
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    mock_quiz.topic = "Geography"
    
    mock_question = MagicMock()
    mock_question.question_text = "What is the capital of France?"
    mock_question.options = ["Berlin", "Paris", "London", "Madrid"]
    mock_question.correct_answer = 1
    
    mock_get_quiz.return_value = (mock_quiz, [mock_question])
    
    # Test the endpoint with auth token
    response = client.get("/api/v1/quiz/1", headers=auth_token)
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert len(data["questions"]) == 1
    assert data["topic"] == "Geography"

@patch('main.get_quiz_with_questions')
def test_get_quiz_not_found(mock_get_quiz, auth_token):
    # Mock the database query to return no quiz
    mock_get_quiz.return_value = (None, None)
    
    # Test the endpoint with auth token
    response = client.get("/api/v1/quiz/999", headers=auth_token)
    
    # Verify the response
    assert response.status_code == 404
    assert "Quiz not found" in response.json()["detail"]

def test_get_quiz_invalid_id(auth_token):
    # Test with invalid quiz ID (non-integer)
    response = client.get("/api/v1/quiz/invalid", headers=auth_token)
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

@patch('main.get_quiz_with_questions')
@patch('main.record_quiz_result')
def test_submit_answers(mock_record_result, mock_get_quiz, auth_token):
    # Mock the database query
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    
    mock_question1 = MagicMock()
    mock_question1.correct_answer = 1
    mock_question2 = MagicMock()
    mock_question2.correct_answer = 2
    
    mock_get_quiz.return_value = (mock_quiz, [mock_question1, mock_question2])
    
    # Test the endpoint with auth token
    response = client.post(
        "/api/v1/submit-answer",
        headers=auth_token,
        json={
            "quiz_id": 1,
            "answers": [1, 3]  # First answer correct, second incorrect
        }
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["quiz_id"] == 1
    assert data["score"] == 1
    assert data["total"] == 2
    assert data["answers"] == [1, 3]
    assert data["correct_answers"] == [1, 2]
    
    # Verify the mock was called correctly
    mock_record_result.assert_called_once()

@patch('main.get_quiz_with_questions')
def test_submit_answers_quiz_not_found(mock_get_quiz, auth_token):
    # Mock the database query to return no quiz
    mock_get_quiz.return_value = (None, None)
    
    # Test the endpoint with auth token
    response = client.post(
        "/api/v1/submit-answer",
        headers=auth_token,
        json={
            "quiz_id": 999,
            "answers": [1, 2]
        }
    )
    
    # Verify the response
    assert response.status_code == 404
    assert "Quiz not found" in response.json()["detail"]

def test_submit_answers_invalid_input(auth_token):
    # Test with missing required field
    response = client.post(
        "/api/v1/submit-answer",
        headers=auth_token,
        json={
            "answers": [1, 2]  # Missing quiz_id
        }
    )
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

def test_cors_preflight():
    # Test the CORS preflight response
    headers = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
        "Origin": "http://localhost:3000"
    }
    response = client.options("/api/v1/generate-quiz", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_register_user(setup_db):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "testuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    assert data["is_active"] is True

def test_register_duplicate_user(setup_db):
    client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "testpassword"}
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "testpassword"}
    )
    assert response.status_code == 400
    assert "already registered" in response.text

def test_login_success(setup_db):
    client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@example.com", "password": "testpassword"}
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "loginuser@example.com", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(setup_db):
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "rightpassword"}
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "wrongpass@example.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.text

def test_protected_route_requires_auth(setup_db):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.text

def test_protected_route_with_token(setup_db):
    client.post(
        "/api/v1/auth/register",
        json={"email": "meuser@example.com", "password": "testpassword"}
    )
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "meuser@example.com", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_resp.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "meuser@example.com" 