import json
from unittest.mock import MagicMock, patch

import pytest

from ai_utils import QuizGenerationError, extract_text_from_pdf, generate_quiz_from_text


class TestAIUtils:
    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_from_text_success(self, mock_openai):
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

        result = generate_quiz_from_text(
            "France is a country in Europe. Paris is its capital."
        )

        assert len(result) > 0
        assert "question" in result[0]
        assert "options" in result[0]
        assert "correct_answer" in result[0]
        assert mock_openai.called

    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_json_error(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not JSON"
        mock_openai.return_value = mock_response

        with pytest.raises(QuizGenerationError, match="invalid data"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_api_error(self, mock_openai):
        mock_openai.side_effect = Exception("API Error")

        with pytest.raises(QuizGenerationError, match="Quiz generation failed"):
            generate_quiz_from_text("Some text")

    def test_generate_quiz_rejects_empty_text(self):
        with pytest.raises(QuizGenerationError, match="No text was provided"):
            generate_quiz_from_text("   ")

    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_rejects_empty_question_list(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "[]"
        mock_openai.return_value = mock_response

        with pytest.raises(QuizGenerationError, match="no questions"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils.openai.chat.completions.create")
    def test_generate_quiz_rejects_invalid_question_structure(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(
            [{"question": "Missing options"}]
        )
        mock_openai.return_value = mock_response

        with pytest.raises(QuizGenerationError, match="invalid question"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils.fitz.open")
    @patch("ai_utils.tempfile.NamedTemporaryFile")
    @patch("ai_utils.os.unlink")
    def test_extract_text_from_pdf(self, mock_unlink, mock_temp, mock_fitz_open):
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.pdf"
        mock_file.__enter__.return_value = mock_file
        mock_temp.return_value = mock_file

        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello from PDF"
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])
        mock_fitz_open.return_value = mock_doc

        pdf_file = MagicMock()
        pdf_file.read.return_value = b"%PDF-1.5"

        text = extract_text_from_pdf(pdf_file)
        assert text == "Hello from PDF"
        mock_unlink.assert_called_once()
