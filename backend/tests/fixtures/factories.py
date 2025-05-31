"""
Centralized test data factories for QuizNess backend.

This module provides Factory Boy factories for generating realistic test data
across all test suites. It ensures consistency and realism in test data.
"""

import factory
from factory import Faker, SubFactory, LazyFunction, Sequence
from faker import Faker as FakerInstance
import random
from datetime import datetime, timedelta

# Import models
from models.user import User
from models.quiz import Quiz
from models.question import Question
from models.result import Result
from auth.auth_utils import get_password_hash

fake = FakerInstance()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = Sequence(lambda n: f"testuser{n}@example.com")
    hashed_password = LazyFunction(lambda: get_password_hash("testpass123"))
    is_active = True
    
    @classmethod
    def create(cls, session, **kwargs):
        """Create a user with the given session."""
        user = cls.build(**kwargs)
        session.add(user)
        session.flush()
        return user
    
    @classmethod
    def create_batch(cls, size, session, **kwargs):
        """Create multiple users."""
        users = []
        for _ in range(size):
            user = cls.create(session, **kwargs)
            users.append(user)
        return users
    
    class Params:
        # Traits for different user types
        inactive = factory.Trait(is_active=False)
        admin = factory.Trait(email="admin@quizness.com")
        old_password = factory.Trait(
            hashed_password="$2b$12$old.hash.for.testing.purposes.only"
        )


class QuizFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test quizzes."""
    
    class Meta:
        model = Quiz
        sqlalchemy_session_persistence = "commit"
    
    title = Faker("sentence", nb_words=4)
    topic = Faker("word")
    difficulty = factory.Iterator(["easy", "medium", "hard"])
    time_limit = factory.LazyFunction(lambda: random.randint(10, 60))
    published = True
    user = SubFactory(UserFactory)
    
    @classmethod
    def create(cls, session, **kwargs):
        """Create a quiz with the given session."""
        if 'user' not in kwargs:
            user = UserFactory.create(session)
            kwargs['user'] = user
        
        quiz = cls.build(**kwargs)
        session.add(quiz)
        session.flush()
        return quiz
    
    @classmethod
    def create_batch(cls, size, session, **kwargs):
        """Create multiple quizzes."""
        quizzes = []
        for _ in range(size):
            quiz = cls.create(session, **kwargs)
            quizzes.append(quiz)
        return quizzes
    
    class Params:
        # Traits for different quiz types
        easy = factory.Trait(difficulty="easy", time_limit=15)
        medium = factory.Trait(difficulty="medium", time_limit=30)
        hard = factory.Trait(difficulty="hard", time_limit=45)
        unpublished = factory.Trait(published=False)
        with_many_questions = factory.Trait(time_limit=60)


class QuestionFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test questions."""
    
    class Meta:
        model = Question
        sqlalchemy_session_persistence = "commit"
    
    question_text = Faker("sentence", nb_words=8)
    options = LazyFunction(lambda: [
        fake.word().capitalize(),
        fake.word().capitalize(), 
        fake.word().capitalize(),
        fake.word().capitalize()
    ])
    correct_answer = factory.LazyFunction(lambda: random.randint(0, 3))
    order = factory.Sequence(lambda n: n)
    quiz = SubFactory(QuizFactory)
    
    @classmethod
    def create(cls, session, **kwargs):
        """Create a question with the given session."""
        if 'quiz' not in kwargs:
            quiz = QuizFactory.create(session)
            kwargs['quiz'] = quiz
            
        question = cls.build(**kwargs)
        session.add(question)
        session.flush()
        return question
    
    @classmethod
    def create_batch(cls, size, session, **kwargs):
        """Create multiple questions."""
        questions = []
        for i in range(size):
            if 'order' not in kwargs:
                kwargs['order'] = i
            question = cls.create(session, **kwargs)
            questions.append(question)
        return questions
    
    class Params:
        # Traits for different question types
        true_false = factory.Trait(
            options=["True", "False", "", ""],
            correct_answer=factory.LazyFunction(lambda: random.randint(0, 1))
        )
        short_answer = factory.Trait(
            options=[fake.sentence(nb_words=3), "", "", ""],
            correct_answer=0
        )


class ResultFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test quiz results."""
    
    class Meta:
        model = Result
        sqlalchemy_session_persistence = "commit"
    
    score = factory.LazyFunction(lambda: random.randint(0, 100))
    answers = LazyFunction(lambda: [
        {"question_id": i, "selected_answer": random.randint(0, 3)}
        for i in range(1, 6)
    ])
    user = SubFactory(UserFactory)
    quiz = SubFactory(QuizFactory)
    
    @classmethod
    def create(cls, session, **kwargs):
        """Create a result with the given session."""
        if 'user' not in kwargs:
            user = UserFactory.create(session)
            kwargs['user'] = user
        if 'quiz' not in kwargs:
            quiz = QuizFactory.create(session)
            kwargs['quiz'] = quiz
            
        result = cls.build(**kwargs)
        session.add(result)
        session.flush()
        return result
    
    @classmethod
    def create_batch(cls, size, session, **kwargs):
        """Create multiple results."""
        results = []
        for _ in range(size):
            result = cls.create(session, **kwargs)
            results.append(result)
        return results
    
    class Params:
        # Traits for different result types
        perfect_score = factory.Trait(score=100)
        failing_score = factory.Trait(score=factory.LazyFunction(lambda: random.randint(0, 49)))


# Batch creation functions
def create_quiz_with_questions(session, num_questions=5, **quiz_kwargs):
    """Create a quiz with a specified number of questions."""
    quiz = QuizFactory.create(session, **quiz_kwargs)
    questions = QuestionFactory.create_batch(num_questions, session, quiz=quiz)
    return quiz, questions


def create_user_with_quizzes(session, num_quizzes=3, **user_kwargs):
    """Create a user with multiple quizzes."""
    user = UserFactory.create(session, **user_kwargs)
    quizzes = QuizFactory.create_batch(num_quizzes, session, user=user)
    return user, quizzes


def create_complete_quiz_session(session, num_questions=5):
    """Create a complete quiz session with user, quiz, questions, and result."""
    user = UserFactory.create(session)
    quiz, questions = create_quiz_with_questions(session, num_questions, user=user)
    result = ResultFactory.create(session, user=user, quiz=quiz)
    return user, quiz, questions, result


# Test data sets for specific scenarios
class TestDataSets:
    """Pre-configured data sets for common testing scenarios."""
    
    @staticmethod
    def educational_quiz_set(session):
        """Create a set of educational quizzes for testing."""
        teacher = UserFactory.create(session, email="teacher@school.edu")
        
        # Create quizzes for different subjects
        subjects = ["Mathematics", "Science", "History", "Literature"]
        quizzes = []
        
        for subject in subjects:
            quiz, questions = create_quiz_with_questions(
                session,
                num_questions=10,
                topic=subject,
                user=teacher,
                difficulty="medium"
            )
            quizzes.append((quiz, questions))
        
        return teacher, quizzes
    
    @staticmethod
    def corporate_training_set(session):
        """Create a corporate training scenario."""
        trainer = UserFactory.create(session, email="trainer@company.com")
        employees = UserFactory.create_batch(5, session)
        
        # Create training modules
        modules = ["Safety Training", "Compliance", "Leadership"]
        training_data = []
        
        for module in modules:
            quiz, questions = create_quiz_with_questions(
                session,
                num_questions=8,
                topic=module,
                user=trainer,
                difficulty="easy"
            )
            
            # Create results for employees
            results = []
            for employee in employees:
                result = ResultFactory.create(
                    session,
                    user=employee,
                    quiz=quiz,
                    score=random.randint(70, 100)
                )
                results.append(result)
            
            training_data.append((quiz, questions, results))
        
        return trainer, employees, training_data


# Mock responses for external services
class MockResponses:
    """Mock responses for external API calls."""
    
    @staticmethod
    def openai_quiz_generation():
        """Mock OpenAI API response for quiz generation."""
        return {
            "choices": [{
                "message": {
                    "content": '''[
                        {
                            "question": "What is the capital of France?",
                            "options": ["Berlin", "Paris", "London", "Madrid"],
                            "correct_answer": 1
                        },
                        {
                            "question": "Which programming language is known for its simplicity?",
                            "options": ["C++", "Python", "Assembly", "Fortran"],
                            "correct_answer": 1
                        }
                    ]'''
                }
            }]
        }
    
    @staticmethod
    def openai_error_response():
        """Mock OpenAI API error response."""
        return {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error",
                "code": "rate_limit_exceeded"
            }
        }
    
    @staticmethod
    def document_extraction_response():
        """Mock document text extraction response."""
        return """
        Introduction to Machine Learning
        
        Machine learning is a subset of artificial intelligence that focuses on
        algorithms that can learn from and make predictions on data. Key concepts
        include supervised learning, unsupervised learning, and reinforcement learning.
        
        Common algorithms include linear regression, decision trees, and neural networks.
        """


# Alias for backward compatibility
QuizResultFactory = ResultFactory 