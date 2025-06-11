import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
import psutil
import os
from main import app

pytestmark = pytest.mark.slow

client = TestClient(app)


def test_simple_check():
    """Simple test to verify the framework works"""
    assert True


def test_health_check_performance():
    """Test that the health check responds quickly"""
    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "QuizNess API is running"}
    
    # Health check should be very fast (under 100ms)
    response_time = end_time - start_time
    assert response_time < 0.1, f"Health check took {response_time:.3f}s, should be under 0.1s"


@patch('ai_utils.openai.ChatCompletion.create')
def test_quiz_generation_performance(mock_openai):
    """Test quiz generation performance"""
    # Mock OpenAI response
    mock_openai.return_value.choices = [
        type('obj', (object,), {
            'message': type('obj', (object,), {
                'content': '''[
                    {
                        "question": "What is the capital of France?",
                        "options": ["London", "Berlin", "Paris", "Madrid"],
                        "correct_answer": "Paris"
                    }
                ]'''
            })()
        })()
    ]
    
    start_time = time.time()
    response = client.post(
        "/quizzes/",
        json={
            "title": "Test Quiz",
            "text_input": "France is a country in Europe. The capital of France is Paris."
        },
        headers={"Authorization": "Bearer fake_token"}
    )
    end_time = time.time()
    
    assert response.status_code == 201
    response_time = end_time - start_time
    # Quiz generation should complete within 5 seconds
    assert response_time < 5.0, f"Quiz generation took {response_time:.3f}s"


def test_concurrent_requests():
    """Test handling of concurrent requests"""
    import threading
    import queue
    
    results = queue.Queue()
    
    def make_request():
        response = client.get("/health")
        results.put((response.status_code, time.time()))
    
    # Start concurrent requests
    threads = []
    start_time = time.time()
    
    for _ in range(10):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # Check all requests succeeded
    success_count = 0
    while not results.empty():
        status_code, _ = results.get()
        if status_code == 200:
            success_count += 1
    
    assert success_count == 10, f"Only {success_count}/10 requests succeeded"
    
    # All 10 concurrent requests should complete within 2 seconds
    total_time = end_time - start_time
    assert total_time < 2.0, f"Concurrent requests took {total_time:.3f}s"


def test_quiz_retrieval_performance(client):
    """Test quiz retrieval performance with database queries"""
    # Create a test quiz first
    with patch('ai_utils.openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value.choices = [
            type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': '''[
                        {
                            "question": "Test question?",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "A"
                        }
                    ]'''
                })()
            })()
        ]
        
        create_response = client.post(
            "/quizzes/",
            json={
                "title": "Performance Test Quiz",
                "text_input": "Test content for performance testing."
            },
            headers={"Authorization": "Bearer fake_token"}
        )
        quiz_id = create_response.json()["id"]
    
    # Test retrieval performance
    start_time = time.time()
    response = client.get(f"/quizzes/{quiz_id}")
    end_time = time.time()
    
    assert response.status_code == 200
    response_time = end_time - start_time
    # Quiz retrieval should be very fast (under 200ms)
    assert response_time < 0.2, f"Quiz retrieval took {response_time:.3f}s"


def test_memory_usage_with_large_quiz():
    """Test memory usage doesn't spike with larger operations"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Make multiple requests to simulate load
    for _ in range(20):
        response = client.get("/health")
        assert response.status_code == 200
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (under 50MB for these simple operations)
    assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB"


def test_database_query_performance(client):
    """Test that database queries are performant"""
    # This test checks that we can handle multiple database operations efficiently
    start_time = time.time()
    
    # Make multiple requests that involve database operations
    for _ in range(5):
        response = client.get("/quizzes/")
        assert response.status_code == 200
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 5 database queries should complete quickly (under 1 second)
    assert total_time < 1.0, f"5 database queries took {total_time:.3f}s"
