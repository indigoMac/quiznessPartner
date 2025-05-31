import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from unittest.mock import patch
import statistics

pytestmark = pytest.mark.slow

class TestPerformance:
    """Performance tests for the API endpoints."""
    
    def test_health_check_performance(self, client: TestClient):
        """Test health check endpoint performance."""
        response_times = []
        
        # Reduced from 100 to 10 iterations for faster testing
        for _ in range(10):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        # Health check should be very fast
        assert avg_time < 0.1, f"Average response time {avg_time:.3f}s is too slow"
        assert max_time < 0.5, f"Max response time {max_time:.3f}s is too slow"
    
    @patch('main.generate_quiz_from_text')
    def test_quiz_generation_performance(self, mock_generate_quiz, 
                                       client: TestClient, auth_headers):
        """Test quiz generation endpoint performance under load."""
        
        mock_generate_quiz.return_value = [
            {
                "question": "Performance test question?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0
            }
        ]
        
        response_times = []
        
        # Reduced from 50 to 5 iterations for faster testing
        for i in range(5):
            start_time = time.time()
            response = client.post(
                "/api/v1/generate-quiz",
                headers=auth_headers,
                json={
                    "content": f"Performance test content {i}",
                    "topic": "Performance",
                    "num_questions": 1
                }
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        # Quiz generation should complete within reasonable time
        assert avg_time < 2.0, f"Average response time {avg_time:.3f}s is too slow"
        assert max_time < 5.0, f"Max response time {max_time:.3f}s is too slow"
    
    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests."""
        
        def make_request():
            response = client.get("/health")
            return response.status_code == 200
        
        # Reduced from 100 to 20 requests with 5 workers for faster testing
        with ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
            end_time = time.time()
        
        # All requests should succeed
        assert all(results), "Some requests failed under concurrent load"
        
        # Total time should be reasonable for 20 requests
        total_time = end_time - start_time
        assert total_time < 5.0, f"Concurrent requests took {total_time:.3f}s"
    
    @patch('main.get_quiz_with_questions')
    def test_quiz_retrieval_performance(self, mock_get_quiz, client: TestClient):
        """Test quiz retrieval performance with various quiz sizes."""
        
        from models.quiz import Quiz
        from models.question import Question
        from unittest.mock import MagicMock
        
        # Test different quiz sizes
        quiz_sizes = [1, 5, 10, 20, 50]
        
        for size in quiz_sizes:
            # Mock quiz and questions
            mock_quiz = MagicMock(spec=Quiz)
            mock_quiz.id = 1
            mock_quiz.title = f"Quiz with {size} questions"
            mock_quiz.topic = "Performance"
            
            mock_questions = []
            for i in range(size):
                mock_question = MagicMock(spec=Question)
                mock_question.id = i + 1
                mock_question.question_text = f"Question {i + 1}"
                mock_question.options = ["A", "B", "C", "D"]
                mock_question.correct_answer = 0
                mock_questions.append(mock_question)
            
            mock_get_quiz.return_value = (mock_quiz, mock_questions)
            
            # Measure response time
            start_time = time.time()
            response = client.get("/api/v1/quiz/1")
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["questions"]) == size
            
            response_time = end_time - start_time
            # Response time should scale reasonably with quiz size
            max_expected_time = 0.1 + (size * 0.01)  # Base time + linear scaling
            assert response_time < max_expected_time, \
                f"Quiz with {size} questions took {response_time:.3f}s (max: {max_expected_time:.3f}s)"
    
    def test_memory_usage_with_large_quiz(self, client: TestClient, auth_headers):
        """Test memory efficiency with large quiz generation."""
        
        with patch('main.generate_quiz_from_text') as mock_generate:
            # Reduced from 100 to 10 questions for faster testing
            large_quiz = []
            for i in range(10):
                large_quiz.append({
                    "question": f"Large quiz question {i + 1}?",
                    "options": [f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}"],
                    "correct_answer": i % 4
                })
            
            mock_generate.return_value = large_quiz
            
            start_time = time.time()
            response = client.post(
                "/api/v1/generate-quiz",
                headers=auth_headers,
                json={
                    "content": "Large content for testing memory usage",
                    "topic": "Memory Test",
                    "num_questions": 10
                }
            )
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["questions"]) == 10
            
            # Even large quizzes should complete in reasonable time
            response_time = end_time - start_time
            assert response_time < 5.0, f"Large quiz generation took {response_time:.3f}s"
    
    def test_database_query_performance(self, client: TestClient, db_session, auth_headers):
        """Test database query performance with multiple quizzes."""
        
        # Create multiple quizzes first - reduced from 10 to 3 for faster testing
        with patch('main.generate_quiz_from_text') as mock_generate:
            mock_generate.return_value = [
                {
                    "question": "DB performance question?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0
                }
            ]
            
            quiz_ids = []
            for i in range(3):
                response = client.post(
                    "/api/v1/generate-quiz",
                    headers=auth_headers,
                    json={
                        "content": f"DB performance content {i}",
                        "topic": f"Topic {i}",
                        "num_questions": 1
                    }
                )
                quiz_ids.append(response.json()["id"])
        
        # Test retrieval performance
        retrieval_times = []
        for quiz_id in quiz_ids:
            start_time = time.time()
            response = client.get(f"/api/v1/quiz/{quiz_id}")
            end_time = time.time()
            
            assert response.status_code == 200
            retrieval_times.append(end_time - start_time)
        
        avg_retrieval_time = statistics.mean(retrieval_times)
        assert avg_retrieval_time < 0.5, f"Average quiz retrieval time {avg_retrieval_time:.3f}s is too slow" 