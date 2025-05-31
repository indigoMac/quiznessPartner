import json
from unittest.mock import MagicMock, patch

import pytest

from ai_utils import (extract_text_from_pdf, generate_quiz_from_text,
                      get_fallback_questions)


class TestAIUtils:
    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_from_text_success(self, mock_openai):
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "question": "What is the capital of France?",
                    "options": ["Berlin", "Paris", "London", "Madrid"],
                    "correct_answer": 1,
                }
            ]
        )
        mock_openai.return_value = mock_response

        # Call the function
        result = generate_quiz_from_text(
            "France is a country in Europe. Paris is its capital."
        )

        # Verify the result
        assert len(result) > 0
        assert "question" in result[0]
        assert "options" in result[0]
        assert "correct_answer" in result[0]
        assert mock_openai.called

    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_json_error(self, mock_openai):
        # Prepare mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not JSON"
        mock_openai.return_value = mock_response

        # Call the function
        result = generate_quiz_from_text("Some text")

        # It should return fallback questions
        assert len(result) > 0
        assert "question" in result[0]
        assert "options" in result[0]
        assert isinstance(result[0]["options"], list)
        assert "correct_answer" in result[0]

    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_api_error(self, mock_openai):
        # Make the API call raise an exception
        mock_openai.side_effect = Exception("API Error")

        # Call the function
        result = generate_quiz_from_text("Some text")

        # It should return fallback questions
        assert len(result) > 0
        assert "question" in result[0]
        assert "options" in result[0]

    def test_get_fallback_questions(self):
        # Test with topic
        topic = "Science"
        result = get_fallback_questions(topic)
        assert len(result) > 0
        assert topic in result[0]["question"]

        # Test without topic
        result = get_fallback_questions()
        assert len(result) > 0
        assert "this subject" in result[0]["question"]
