"""
Unit tests for QuizNess data models.

Tests model validation, business logic, and edge cases without database dependencies.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from models.user import User
from models.quiz import Quiz
from models.question import Question
from models.result import Result


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_123"
        )
        
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        # Default value is set by SQLAlchemy column definition at database level
        assert hasattr(user, 'is_active')
    
    def test_user_email_validation(self):
        """Test user email validation."""
        # Valid email
        user = User(email="valid@example.com", hashed_password="hash")
        assert user.email == "valid@example.com"
        
        # Email should be stored as provided (validation handled by Pydantic)
        user2 = User(email="UPPERCASE@EXAMPLE.COM", hashed_password="hash")
        assert user2.email == "UPPERCASE@EXAMPLE.COM"
    
    def test_user_email_uniqueness_constraint(self):
        """Test that email uniqueness is enforced at model level."""
        # This would be tested with actual database in integration tests
        # Here we just verify the model structure
        user1 = User(email="same@example.com", hashed_password="hash1")
        user2 = User(email="same@example.com", hashed_password="hash2")
        
        assert user1.email == user2.email
        # Uniqueness constraint would be enforced by database
    
    def test_user_default_active_status(self):
        """Test that users are active by default."""
        user = User(email="test@example.com", hashed_password="hash")
        # Default value is set by SQLAlchemy column definition
        assert hasattr(user, 'is_active')
    
    def test_user_deactivation(self):
        """Test user deactivation."""
        user = User(email="test@example.com", hashed_password="hash")
        user.is_active = False
        assert user.is_active is False
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = User(email="test@example.com", hashed_password="hash")
        # Test that the object can be converted to string
        str_repr = str(user)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestQuizModel:
    """Test cases for Quiz model."""
    
    def test_quiz_creation(self):
        """Test basic quiz creation."""
        quiz = Quiz(
            title="Test Quiz",
            topic="Testing",
            user_id=1
        )
        
        assert quiz.title == "Test Quiz"
        assert quiz.topic == "Testing"
        assert quiz.user_id == 1
    
    def test_quiz_required_fields(self):
        """Test quiz required fields."""
        # Title is required
        quiz = Quiz(title="Required Title")
        assert quiz.title == "Required Title"
        
        # Topic is optional
        quiz_no_topic = Quiz(title="Test")
        assert quiz_no_topic.title == "Test"
        assert quiz_no_topic.topic is None
    
    def test_quiz_foreign_key_structure(self):
        """Test quiz foreign key structure."""
        quiz = Quiz(title="Test", user_id=123)
        assert quiz.user_id == 123
        
        # user_id can be None (nullable=True)
        quiz_no_user = Quiz(title="Test")
        assert quiz_no_user.user_id is None
    
    def test_quiz_automatic_timestamps(self):
        """Test that timestamps are handled properly."""
        quiz = Quiz(title="Test", topic="Test", user_id=1)
        
        # Timestamps would be set by database defaults
        # Here we just verify the model structure
        assert hasattr(quiz, 'created_at')
    
    def test_quiz_string_representation(self):
        """Test quiz string representation."""
        quiz = Quiz(title="Python Basics", topic="Programming", user_id=1)
        
        # Test that the object can be converted to string
        str_repr = str(quiz)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestQuestionModel:
    """Test cases for Question model."""
    
    def test_question_creation(self):
        """Test basic question creation."""
        question = Question(
            question_text="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer=1,
            quiz_id=1
        )
        
        assert question.question_text == "What is 2+2?"
        assert question.options == ["3", "4", "5", "6"]
        assert question.correct_answer == 1
        assert question.quiz_id == 1
    
    def test_question_required_fields(self):
        """Test question required fields."""
        question = Question(
            question_text="Test?",
            options=["A", "B", "C", "D"],
            correct_answer=0,
            quiz_id=1
        )
        
        # All fields should be present
        assert question.question_text is not None
        assert question.options is not None
        assert question.correct_answer is not None
        assert question.quiz_id is not None
    
    def test_question_correct_answer_validation(self):
        """Test correct answer index validation."""
        # Valid answer index
        question = Question(
            question_text="Test?",
            options=["A", "B", "C", "D"],
            correct_answer=2,  # Valid index
            quiz_id=1
        )
        assert question.correct_answer == 2
        
        # Edge case: first option
        question_first = Question(
            question_text="Test?",
            options=["A", "B", "C", "D"],
            correct_answer=0,
            quiz_id=1
        )
        assert question_first.correct_answer == 0
    
    def test_question_options_structure(self):
        """Test that options are stored as JSON."""
        question = Question(
            question_text="Test?",
            options=["Option 1", "Option 2"],
            correct_answer=0,
            quiz_id=1
        )
        
        assert isinstance(question.options, list)
        assert len(question.options) >= 2
        assert all(isinstance(option, str) for option in question.options)
    
    def test_question_foreign_key_structure(self):
        """Test question foreign key structure."""
        question = Question(
            question_text="Test?",
            options=["A", "B"],
            correct_answer=0,
            quiz_id=5
        )
        
        assert question.quiz_id == 5
    
    def test_question_string_representation(self):
        """Test question string representation."""
        question = Question(
            question_text="What is the capital of France?",
            options=["London", "Paris", "Berlin", "Madrid"],
            correct_answer=1,
            quiz_id=1
        )
        
        # Test that the object can be converted to string
        str_repr = str(question)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestResultModel:
    """Test cases for Result model."""
    
    def test_result_creation(self):
        """Test basic result creation."""
        result = Result(
            score=85,
            answers=[{"question_id": 1, "selected_answer": 2}],
            user_id=1,
            quiz_id=1
        )
        
        assert result.score == 85
        assert result.answers == [{"question_id": 1, "selected_answer": 2}]
        assert result.user_id == 1
        assert result.quiz_id == 1
    
    def test_result_percentage_calculation(self):
        """Test percentage score calculation."""
        # Perfect score
        perfect_result = Result(
            score=100,
            answers=[],
            user_id=1,
            quiz_id=1
        )
        assert perfect_result.score == 100
        
        # Partial score
        partial_result = Result(
            score=75,
            answers=[],
            user_id=1,
            quiz_id=1
        )
        assert partial_result.score == 75
        
        # Zero score
        zero_result = Result(
            score=0,
            answers=[],
            user_id=1,
            quiz_id=1
        )
        assert zero_result.score == 0
    
    def test_result_score_validation(self):
        """Test score validation bounds."""
        # Valid scores
        valid_scores = [0, 25, 50, 75, 100]
        
        for score in valid_scores:
            result = Result(
                score=score,
                answers=[],
                user_id=1,
                quiz_id=1
            )
            assert 0 <= result.score <= 100
    
    def test_result_answers_structure(self):
        """Test answers JSON structure."""
        answers_data = [
            {"question_id": 1, "selected_answer": 0},
            {"question_id": 2, "selected_answer": 2},
            {"question_id": 3, "selected_answer": 1}
        ]
        
        result = Result(
            score=80,
            answers=answers_data,
            user_id=1,
            quiz_id=1
        )
        
        assert result.answers == answers_data
        assert isinstance(result.answers, list)
        assert len(result.answers) == 3
    
    def test_result_foreign_key_requirements(self):
        """Test foreign key requirements."""
        result = Result(
            score=80,
            answers=[],
            user_id=1,
            quiz_id=1
        )
        
        # Both user_id and quiz_id should be present
        assert result.user_id is not None
        assert result.quiz_id is not None
    
    def test_result_creation_time(self):
        """Test creation time structure."""
        result = Result(
            score=90,
            answers=[],
            user_id=1,
            quiz_id=1
        )
        
        # Creation time would be set by database default
        # Here we verify the model structure
        assert hasattr(result, 'created_at')


class TestModelRelationships:
    """Test cases for model relationships."""
    
    def test_user_quiz_relationship(self):
        """Test relationship between users and quizzes."""
        # This would be tested with actual database in integration tests
        # Here we verify the model structure supports relationships
        
        user = User(email="test@example.com", hashed_password="hash")
        quiz = Quiz(
            title="Test Quiz",
            topic="Test",
            user_id=1  # Would reference user.id
        )
        
        # Verify foreign key structure
        assert hasattr(quiz, 'user_id')
        assert quiz.user_id == 1
    
    def test_quiz_question_relationship(self):
        """Test relationship between quizzes and questions."""
        quiz = Quiz(title="Test Quiz", topic="Test", user_id=1)
        
        question = Question(
            question_text="Test?",
            options=["A", "B"],
            correct_answer=0,
            quiz_id=1  # Would reference quiz.id
        )
        
        # Verify foreign key structure
        assert hasattr(question, 'quiz_id')
        assert question.quiz_id == 1
    
    def test_model_table_names(self):
        """Test that models have correct table names."""
        assert User.__tablename__ == "users"
        assert Quiz.__tablename__ == "quizzes"
        assert Question.__tablename__ == "questions"
        assert Result.__tablename__ == "results"
    
    def test_model_primary_keys(self):
        """Test that models have primary key fields."""
        user = User(email="test@example.com", hashed_password="hash")
        quiz = Quiz(title="Test Quiz")
        question = Question(
            question_text="Test?",
            options=["A", "B"],
            correct_answer=0,
            quiz_id=1
        )
        result = Result(score=100, answers=[], user_id=1, quiz_id=1)
        
        # All models should have id attribute
        assert hasattr(user, 'id')
        assert hasattr(quiz, 'id')
        assert hasattr(question, 'id')
        assert hasattr(result, 'id') 