import pytest
import os
import sys
from unittest.mock import MagicMock

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the fitz module
sys.modules['fitz'] = MagicMock()

# Import fixtures and setup code here that will be shared across tests

@pytest.fixture
def mock_openai_response():
    """Mock response from OpenAI API"""
    return {
        "choices": [
            {
                "message": {
                    "content": """[
                        {
                            "question": "What is the capital of France?",
                            "options": ["Berlin", "Paris", "London", "Madrid"],
                            "correct_answer": 1
                        },
                        {
                            "question": "Who wrote 'Romeo and Juliet'?",
                            "options": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
                            "correct_answer": 1
                        }
                    ]"""
                }
            }
        ]
    } 