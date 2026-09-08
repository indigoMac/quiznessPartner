import json
from unittest.mock import MagicMock, patch

import pytest

from ai_utils import (
    DEFAULT_LLM_BASE_URL,
    GeneratedQuiz,
    QuizGenerationError,
    _llm_base_url,
    _llm_model,
    as_generated_quiz,
    extract_text_from_pdf,
    generate_quiz_from_text,
    select_source_chunks,
)


class TestAIUtils:
    @patch("ai_utils._chat_completion")
    def test_generate_quiz_from_text_success(self, mock_openai):
        mock_openai.return_value = json.dumps(
            [
                {
                    "question": "What is the capital of France?",
                    "options": ["Berlin", "Paris", "London", "Madrid"],
                    "correct_answer": 1,
                }
            ]
        )

        result = generate_quiz_from_text(
            "France is a country in Europe. Paris is its capital."
        )

        assert len(result.questions) > 0
        assert result.title == "What is the capital of France"
        assert result.topic is None
        assert "question" in result.questions[0]
        assert "options" in result.questions[0]
        assert "correct_answer" in result.questions[0]
        assert mock_openai.called

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_uses_llm_title_and_topic(self, mock_openai):
        mock_openai.return_value = json.dumps(
            {
                "title": "European Capitals",
                "topic": "Geography",
                "questions": [
                    {
                        "question": "What is the capital of France?",
                        "options": ["Berlin", "Paris", "London", "Madrid"],
                        "correct_answer": 1,
                    }
                ],
            }
        )

        result = generate_quiz_from_text(
            "France is a country in Europe. Paris is its capital."
        )

        assert result.title == "European Capitals"
        assert result.topic == "Geography"
        assert len(result.questions) == 1

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_prefers_requested_topic(self, mock_openai):
        mock_openai.return_value = json.dumps(
            {
                "title": "European Capitals",
                "topic": "World Geography",
                "questions": [
                    {
                        "question": "What is the capital of France?",
                        "options": ["Berlin", "Paris", "London", "Madrid"],
                        "correct_answer": 1,
                    }
                ],
            }
        )

        result = generate_quiz_from_text(
            "France is a country in Europe. Paris is its capital.",
            topic="Geography",
        )

        assert result.title == "European Capitals"
        assert result.topic == "Geography"

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_avoids_existing_questions(self, mock_openai):
        mock_openai.return_value = json.dumps(
            {
                "title": "More Capitals",
                "topic": "Geography",
                "questions": [
                    {
                        "question": "What is the capital of France?",
                        "options": ["Berlin", "Paris", "London", "Madrid"],
                        "correct_answer": 1,
                    },
                    {
                        "question": "What is the capital of Spain?",
                        "options": ["Lisbon", "Madrid", "Rome", "Paris"],
                        "correct_answer": 1,
                    },
                ],
            }
        )

        result = generate_quiz_from_text(
            "France and Spain are in Europe.",
            topic="Geography",
            num_questions=2,
            existing_questions=[
                {
                    "question": "What is the capital of France?",
                    "options": ["Berlin", "Paris", "London", "Madrid"],
                    "correct_answer": 1,
                }
            ],
        )

        assert [item["question"] for item in result.questions] == [
            "What is the capital of Spain?"
        ]

    def test_as_generated_quiz_accepts_question_lists(self):
        questions = [
            {
                "question": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": 1,
            }
        ]
        result = as_generated_quiz(questions, requested_topic="Math")
        assert isinstance(result, GeneratedQuiz)
        assert result.title == "Quiz on Math"
        assert result.topic == "Math"
        assert result.questions == questions

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_json_error(self, mock_openai):
        mock_openai.return_value = "This is not JSON"

        with pytest.raises(QuizGenerationError, match="invalid data"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_api_error(self, mock_openai):
        mock_openai.side_effect = Exception("API Error")

        with pytest.raises(QuizGenerationError, match="Quiz generation failed"):
            generate_quiz_from_text("Some text")

    def test_generate_quiz_rejects_empty_text(self):
        with pytest.raises(QuizGenerationError, match="No text was provided"):
            generate_quiz_from_text("   ")

    def test_defaults_to_groq(self):
        assert _llm_base_url() == DEFAULT_LLM_BASE_URL
        assert _llm_model() == "openai/gpt-oss-20b"

    def test_maps_deprecated_groq_model(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "llama-3.1-8b-instant")
        assert _llm_model() == "openai/gpt-oss-20b"

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_rejects_empty_question_list(self, mock_openai):
        mock_openai.return_value = "[]"

        with pytest.raises(QuizGenerationError, match="no questions"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_rejects_invalid_question_structure(self, mock_openai):
        mock_openai.return_value = json.dumps([{"question": "Missing options"}])

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

    def test_select_source_chunks_keeps_short_text(self):
        text = "Short source material about rivers."
        assert select_source_chunks(text) == [text]

    def test_select_source_chunks_spreads_long_text(self):
        text = "This is a reasonably long test sentence used for chunking. " * 200
        chunks = select_source_chunks(text, chunk_size=800, max_chunks=4)
        assert 2 <= len(chunks) <= 4
        assert chunks[0] != chunks[-1]

    @patch("ai_utils._chat_completion")
    def test_generate_quiz_uses_multiple_chunks(self, mock_openai):
        long_text = "This is a reasonably long test sentence used for chunking. " * 100
        mock_openai.side_effect = [
            json.dumps(
                {
                    "title": "Chunked Source Quiz",
                    "topic": "Study Notes",
                    "questions": [
                        {
                            "question": "Question from the opening?",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": 0,
                        },
                        {
                            "question": "Another opening question?",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": 1,
                        },
                    ],
                }
            ),
            json.dumps(
                [
                    {
                        "question": "Question from later in the notes?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 2,
                    }
                ]
            ),
        ]

        result = generate_quiz_from_text(long_text, num_questions=3)

        assert result.title == "Chunked Source Quiz"
        assert result.topic == "Study Notes"
        assert len(result.questions) == 3
        assert mock_openai.call_count >= 2
        assert {item["question"] for item in result.questions} == {
            "Question from the opening?",
            "Another opening question?",
            "Question from later in the notes?",
        }
