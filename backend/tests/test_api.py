import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base
from unittest.mock import patch, MagicMock, ANY
import io
import json

from main import app
from db_utils import get_db
from models.quiz import Quiz
from models.question import Question
from models.result import Result
from models.user import User

# Create a test database in memory
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
Base = declarative_base()
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

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch('main.generate_quiz_from_text')
@patch('main.create_quiz')
@patch('main.add_questions_to_quiz')
def test_generate_quiz(mock_add_questions, mock_create_quiz, mock_generate_quiz, setup_db):
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
    
    # Test the endpoint
    response = client.post(
        "/api/v1/generate-quiz",
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
def test_generate_quiz_error(mock_generate_quiz, setup_db):
    # Mock the quiz generation to raise an exception
    mock_generate_quiz.side_effect = Exception("Failed to generate quiz")
    
    # Test the endpoint
    response = client.post(
        "/api/v1/generate-quiz",
        json={"content": "Test content", "topic": "Geography", "num_questions": 1}
    )
    
    # Verify the response
    assert response.status_code == 500
    assert "Error generating quiz" in response.json()["detail"]

def test_generate_quiz_invalid_input():
    # Test with missing required field
    response = client.post(
        "/api/v1/generate-quiz",
        json={"topic": "Geography", "num_questions": 1}  # Missing 'content'
    )
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

@patch('main.extract_text_from_pdf')
@patch('main.generate_quiz_from_text')
@patch('main.create_quiz')
@patch('main.add_questions_to_quiz')
def test_upload_document(mock_add_questions, mock_create_quiz, mock_generate_quiz, mock_extract_text, setup_db):
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
    
    # Test the endpoint
    response = client.post(
        "/api/v1/upload-document",
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
def test_upload_document_extraction_error(mock_extract_text, setup_db):
    # Mock the text extraction to raise an exception
    mock_extract_text.side_effect = Exception("Failed to extract text")
    
    # Create a mock PDF file
    pdf_content = io.BytesIO(b"%PDF-1.5 mock pdf content")
    
    # Test the endpoint
    response = client.post(
        "/api/v1/upload-document",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"topic": "Geography", "num_questions": "3"}
    )
    
    # Verify the response
    assert response.status_code == 500
    assert "Error processing document" in response.json()["detail"]

def test_upload_document_no_file():
    # Test without uploading a file
    response = client.post(
        "/api/v1/upload-document",
        files={},  # No file
        data={"topic": "Geography", "num_questions": "3"}
    )
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

@patch('main.get_quiz_with_questions')
def test_get_quiz(mock_get_quiz, setup_db):
    # Mock the database query
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    mock_quiz.topic = "Geography"
    
    mock_question = MagicMock()
    mock_question.question_text = "What is the capital of France?"
    mock_question.options = ["Berlin", "Paris", "London", "Madrid"]
    mock_question.correct_answer = 1
    
    mock_get_quiz.return_value = (mock_quiz, [mock_question])
    
    # Test the endpoint
    response = client.get("/api/v1/quiz/1")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["topic"] == "Geography"
    assert len(data["questions"]) == 1
    assert data["questions"][0]["question"] == "What is the capital of France?"
    
    # Verify the mock was called correctly
    mock_get_quiz.assert_called_once_with(ANY, 1)

@patch('main.get_quiz_with_questions')
def test_get_quiz_not_found(mock_get_quiz, setup_db):
    # Mock the database query to return no quiz
    mock_get_quiz.return_value = (None, [])
    
    # Test the endpoint
    response = client.get("/api/v1/quiz/999")
    
    # Verify the response
    assert response.status_code == 404
    assert "Quiz not found" in response.json()["detail"]

def test_get_quiz_invalid_id():
    # Test with invalid quiz ID (non-integer)
    response = client.get("/api/v1/quiz/invalid")
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity

@patch('main.get_quiz_with_questions')
@patch('main.record_quiz_result')
def test_submit_answers(mock_record_result, mock_get_quiz, setup_db):
    # Mock the database query
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    
    mock_question1 = MagicMock()
    mock_question1.correct_answer = 1
    
    mock_question2 = MagicMock()
    mock_question2.correct_answer = 2
    
    mock_question3 = MagicMock()
    mock_question3.correct_answer = 0
    
    mock_get_quiz.return_value = (mock_quiz, [mock_question1, mock_question2, mock_question3])
    
    # Test the endpoint with some correct and some incorrect answers
    response = client.post(
        "/api/v1/submit-answer",
        json={"quiz_id": 1, "answers": [1, 0, 0]}  # First and last are correct
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["quiz_id"] == 1
    assert data["score"] == 2  # Two correct answers
    assert data["total"] == 3
    assert data["answers"] == [1, 0, 0]
    assert data["correct_answers"] == [1, 2, 0]
    
    # Verify the mock was called correctly
    mock_record_result.assert_called_once_with(ANY, quiz_id=1, answers=[1, 0, 0], score=2)

@patch('main.get_quiz_with_questions')
def test_submit_answers_quiz_not_found(mock_get_quiz, setup_db):
    # Mock the database query to return no quiz
    mock_get_quiz.return_value = (None, [])
    
    # Test the endpoint
    response = client.post(
        "/api/v1/submit-answer",
        json={"quiz_id": 999, "answers": [0, 1, 2]}
    )
    
    # Verify the response
    assert response.status_code == 404
    assert "Quiz not found" in response.json()["detail"]

def test_submit_answers_invalid_input():
    # Test with missing required field
    response = client.post(
        "/api/v1/submit-answer",
        json={"quiz_id": 1}  # Missing 'answers'
    )
    
    # Verify the response
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test with invalid quiz_id type
    response = client.post(
        "/api/v1/submit-answer",
        json={"quiz_id": "invalid", "answers": [0, 1, 2]}
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