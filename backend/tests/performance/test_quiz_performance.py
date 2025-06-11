"""
Professional performance tests for QuizNess backend.

These tests focus on actual performance bottlenecks:
- Database query performance
- Text processing performance  
- Memory usage patterns
- Function-level performance (not API endpoints)
"""

import time
import pytest
import psutil
import os
from unittest.mock import patch, MagicMock

# Test actual functions that exist
from ai_utils import split_text, get_fallback_questions, generate_quiz_from_text
from db_utils import create_quiz, get_quiz, add_questions_to_quiz

pytestmark = pytest.mark.slow


def test_simple_check():
    """Simple test to verify the framework works"""
    assert True


def test_text_splitting_performance():
    """Test performance of text splitting with large documents"""
    # Create large text document
    large_text = "This is a test sentence. " * 1000  # ~25,000 chars
    
    # Measure splitting performance
    start_time = time.time()
    chunks = split_text(large_text, chunk_size=3000, chunk_overlap=200)
    end_time = time.time()
    
    # Should split large text quickly
    splitting_time = end_time - start_time
    assert splitting_time < 0.1, f"Splitting large text took {splitting_time:.3f}s"
    assert len(chunks) > 1  # Should create multiple chunks
    assert all(len(chunk) <= 3000 for chunk in chunks)  # Respect chunk size


def test_fallback_questions_performance():
    """Test performance of fallback question generation"""
    start_time = time.time()
    
    # Generate fallback questions multiple times
    for i in range(100):
        questions = get_fallback_questions(f"topic_{i}")
        assert len(questions) == 2
        assert all("question" in q and "options" in q and "correct_answer" in q for q in questions)
    
    end_time = time.time()
    
    generation_time = end_time - start_time
    # Should generate 100 sets of fallback questions quickly
    assert generation_time < 0.1, f"Generating 100 fallback question sets took {generation_time:.3f}s"


def test_database_operations_performance(db_session):
    """Test database operations performance with proper session"""
    user_id = 1  # Mock user ID
    
    # Test quiz creation performance
    start_time = time.time()
    quiz = create_quiz(
        db_session,
        title="Performance Test Quiz",
        topic="Performance Testing",
        user_id=user_id
    )
    db_session.commit()
    end_time = time.time()
    
    creation_time = end_time - start_time
    assert creation_time < 0.1, f"Quiz creation took {creation_time:.3f}s"
    
    # Test adding multiple questions performance
    questions_data = []
    for i in range(20):
        questions_data.append({
            "question": f"Database performance question {i}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0
        })
    
    start_time = time.time()
    add_questions_to_quiz(db_session, quiz.id, questions_data)
    db_session.commit()
    end_time = time.time()
    
    questions_time = end_time - start_time
    assert questions_time < 0.2, f"Adding 20 questions took {questions_time:.3f}s"
    
    # Test quiz retrieval performance
    start_time = time.time()
    retrieved_quiz = get_quiz(db_session, quiz.id)
    end_time = time.time()
    
    retrieval_time = end_time - start_time
    assert retrieval_time < 0.05, f"Quiz retrieval took {retrieval_time:.3f}s"
    assert retrieved_quiz.id == quiz.id


def test_memory_usage_with_large_text_processing():
    """Test memory usage patterns with large text processing"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Process large text documents
    large_texts = []
    for i in range(10):
        # Create 10 large text documents
        large_text = f"Document {i}. " + "This is test content. " * 1000
        large_texts.append(large_text)
    
    # Process all texts
    all_chunks = []
    for text in large_texts:
        chunks = split_text(text, chunk_size=2000)
        all_chunks.extend(chunks)
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable for text processing
    assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB"
    assert len(all_chunks) > 10  # Should have created chunks


def test_multiple_database_operations(db_session):
    """Test database performance under load"""
    user_id = 1
    quiz_ids = []
    
    # Create multiple quizzes
    start_time = time.time()
    for i in range(10):
        quiz = create_quiz(
            db_session,
            title=f"Performance Quiz {i}",
            topic=f"Topic {i}",
            user_id=user_id
        )
        db_session.commit()
        quiz_ids.append(quiz.id)
    end_time = time.time()
    
    creation_time = end_time - start_time
    assert creation_time < 1.0, f"Creating 10 quizzes took {creation_time:.3f}s"
    
    # Retrieve all quizzes
    start_time = time.time()
    retrieved_quizzes = []
    for quiz_id in quiz_ids:
        quiz = get_quiz(db_session, quiz_id)
        retrieved_quizzes.append(quiz)
    end_time = time.time()
    
    retrieval_time = end_time - start_time
    assert retrieval_time < 0.5, f"Retrieving 10 quizzes took {retrieval_time:.3f}s"
    assert len(retrieved_quizzes) == 10


@patch('ai_utils.openai.chat.completions.create')
def test_ai_processing_performance_with_mock(mock_openai):
    """Test AI processing performance with proper mocking"""
    # Mock OpenAI response with proper structure
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '''[
        {
            "question": "What is the main topic?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": 0
        },
        {
            "question": "Which option is correct?",
            "options": ["First", "Second", "Third", "Fourth"],
            "correct_answer": 1
        }
    ]'''
    mock_openai.return_value = mock_response
    
    start_time = time.time()
    result = generate_quiz_from_text("Test content for AI processing", topic="Performance", num_questions=2)
    end_time = time.time()
    
    processing_time = end_time - start_time
    # With mocked AI, this should be very fast
    assert processing_time < 0.1, f"AI processing took {processing_time:.3f}s"
    assert len(result) == 2
    assert all("question" in q and "options" in q and "correct_answer" in q for q in result)


def test_text_chunking_with_various_sizes():
    """Test text chunking performance with different sizes"""
    base_text = "This is a sentence for testing. "
    sizes = [100, 1000, 5000, 10000]  # Different text lengths
    
    for size in sizes:
        text = base_text * (size // len(base_text))
        
        start_time = time.time()
        chunks = split_text(text, chunk_size=3000, chunk_overlap=200)
        end_time = time.time()
        
        chunking_time = end_time - start_time
        # Chunking should scale reasonably with text size
        max_expected_time = 0.01 + (size / 100000)  # Linear scaling expectation
        assert chunking_time < max_expected_time, f"Chunking {size} chars took {chunking_time:.3f}s"
        assert len(chunks) >= 1
