import json
from unittest.mock import MagicMock, patch

import pytest

from ai_utils import (
    DEFAULT_LLM_BASE_URL,
    QUIZ_SCHEMA,
    ExplanationError,
    GeneratedQuiz,
    QuizGenerationError,
    _llm_base_url,
    _llm_model,
    _response_format,
    as_generated_quiz,
    explain_quiz_question,
    extract_text_from_pdf,
    generate_quiz_from_text,
    select_explanation_context,
    select_source_chunks,
)


def _question(text: str, correct_answer: int = 0) -> dict:
    return {
        "question": text,
        "options": ["A", "B", "C", "D"],
        "correct_answer": correct_answer,
    }


def _quiz_payload(*questions: dict) -> str:
    return json.dumps(
        {"title": "Sample Quiz", "topic": "Sample", "questions": list(questions)}
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


class TestQuestionCount:
    """The requested number of questions should survive short model replies."""

    @patch("ai_utils._chat_completion")
    def test_tops_up_when_model_returns_too_few(self, mock_openai):
        mock_openai.side_effect = [
            _quiz_payload(_question("Q1?"), _question("Q2?")),
            _quiz_payload(_question("Q3?"), _question("Q4?"), _question("Q5?")),
        ]

        result = generate_quiz_from_text("Short source text.", num_questions=5)

        assert len(result.questions) == 5
        assert mock_openai.call_count == 2

    @patch("ai_utils._chat_completion")
    def test_top_up_ignores_repeated_questions(self, mock_openai):
        mock_openai.side_effect = [
            _quiz_payload(_question("Q1?"), _question("Q2?")),
            _quiz_payload(_question("Q2?"), _question("Q3?")),
        ]

        result = generate_quiz_from_text("Short source text.", num_questions=4)

        assert [item["question"] for item in result.questions] == [
            "Q1?",
            "Q2?",
            "Q3?",
        ]

    @patch("ai_utils._chat_completion")
    def test_stops_topping_up_when_no_new_questions_arrive(self, mock_openai):
        mock_openai.return_value = _quiz_payload(_question("Q1?"))

        result = generate_quiz_from_text("Short source text.", num_questions=5)

        assert len(result.questions) == 1
        assert mock_openai.call_count == 2

    @patch("ai_utils._chat_completion")
    def test_reaches_the_count_across_several_short_replies(self, mock_openai):
        """A model that trickles out questions should still fill the request."""
        counter = iter(range(1, 100))
        mock_openai.side_effect = lambda _prompt: _quiz_payload(
            _question(f"Q{next(counter)}?"), _question(f"Q{next(counter)}?")
        )

        result = generate_quiz_from_text("Short source text.", num_questions=7)

        assert len(result.questions) == 7
        assert len({item["question"] for item in result.questions}) == 7

    @patch("ai_utils._chat_completion")
    def test_never_exceeds_the_requested_count(self, mock_openai):
        mock_openai.return_value = _quiz_payload(
            *(_question(f"Q{index}?") for index in range(8))
        )

        result = generate_quiz_from_text("Short source text.", num_questions=3)

        assert len(result.questions) == 3

    @patch("ai_utils._chat_completion")
    def test_survives_a_failed_chunk(self, mock_openai):
        long_text = "This is a reasonably long test sentence used for chunking. " * 100
        mock_openai.side_effect = [
            _quiz_payload(_question("Q1?")),
            "not json at all",
            _quiz_payload(_question("Q2?")),
        ]

        result = generate_quiz_from_text(long_text, num_questions=2)

        assert [item["question"] for item in result.questions] == ["Q1?", "Q2?"]


class TestStructuredOutput:
    def test_requests_a_strict_schema_on_supported_models(self):
        response_format = _response_format("openai/gpt-oss-20b")

        assert response_format is not None
        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["strict"] is True
        assert response_format["json_schema"]["schema"] == QUIZ_SCHEMA

    def test_omits_the_schema_on_unsupported_models(self):
        assert _response_format("some-other-model") is None

    def test_schema_meets_strict_mode_requirements(self):
        question_schema = QUIZ_SCHEMA["properties"]["questions"]["items"]

        for schema in (QUIZ_SCHEMA, question_schema):
            assert schema["additionalProperties"] is False
            assert set(schema["required"]) == set(schema["properties"])

    @patch("ai_utils.OpenAI")
    def test_passes_the_schema_to_the_api(self, mock_openai_class):
        client = mock_openai_class.return_value
        message = MagicMock(content=_quiz_payload(_question("Q?")))
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=message)]
        )

        generate_quiz_from_text("Short source text.", num_questions=1)

        kwargs = client.chat.completions.create.call_args.kwargs
        assert kwargs["response_format"]["json_schema"]["strict"] is True


class TestGenerationMetrics:
    """Generation should report what it cost and whether it fell short."""

    @patch("ai_utils._emit_metrics")
    @patch("ai_utils._chat_completion")
    def test_reports_counts_and_topup_rounds(self, mock_openai, mock_emit):
        mock_openai.side_effect = [
            _quiz_payload(_question("Q1?")),
            _quiz_payload(_question("Q2?"), _question("Q3?")),
        ]

        generate_quiz_from_text("Short source text.", num_questions=3)

        metrics = mock_emit.call_args.args[0]
        assert metrics.requested == 3
        assert metrics.delivered == 3
        assert metrics.chunks == 1
        assert metrics.topup_rounds == 1
        assert metrics.shortfall == 0
        assert metrics.duration_ms > 0

    @patch("ai_utils._emit_metrics")
    @patch("ai_utils._chat_completion")
    def test_reports_shortfall(self, mock_openai, mock_emit):
        mock_openai.return_value = _quiz_payload(_question("Q1?"))

        generate_quiz_from_text("Short source text.", num_questions=5)

        metrics = mock_emit.call_args.args[0]
        assert metrics.delivered == 1
        assert metrics.shortfall == 4

    @patch("ai_utils._emit_metrics")
    @patch("ai_utils._chat_completion")
    def test_reports_metrics_even_when_generation_fails(self, mock_openai, mock_emit):
        mock_openai.side_effect = Exception("API Error")

        with pytest.raises(QuizGenerationError):
            generate_quiz_from_text("Some text")

        assert mock_emit.called
        assert mock_emit.call_args.args[0].delivered == 0

    @patch("ai_utils.OpenAI")
    def test_accumulates_token_usage_from_the_api(self, mock_openai_class):
        client = mock_openai_class.return_value
        message = MagicMock(content=_quiz_payload(_question("Q?")))
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=message)],
            usage=MagicMock(prompt_tokens=120, completion_tokens=45),
        )

        with patch("ai_utils._emit_metrics") as mock_emit:
            generate_quiz_from_text("Short source text.", num_questions=1)

        metrics = mock_emit.call_args.args[0]
        assert metrics.api_calls == 1
        assert metrics.prompt_tokens == 120
        assert metrics.completion_tokens == 45
        assert metrics.models_used == ["openai/gpt-oss-20b"]

    @patch("ai_utils._chat_completion")
    def test_metrics_do_not_leak_between_generations(self, mock_openai):
        mock_openai.return_value = _quiz_payload(_question("Q1?"))
        captured = []

        with patch("ai_utils._emit_metrics", side_effect=captured.append):
            generate_quiz_from_text("Short source text.", num_questions=1)
            generate_quiz_from_text("Short source text.", num_questions=1)

        assert len(captured) == 2
        assert captured[0] is not captured[1]
        assert all(item.requested == 1 for item in captured)


class TestQuestionValidation:
    @patch("ai_utils._chat_completion")
    def test_rejects_correct_answer_outside_the_options(self, mock_openai):
        mock_openai.return_value = json.dumps([_question("Q?", correct_answer=9)])

        with pytest.raises(QuizGenerationError, match="does not match any option"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils._chat_completion")
    def test_rejects_negative_correct_answer(self, mock_openai):
        mock_openai.return_value = json.dumps([_question("Q?", correct_answer=-1)])

        with pytest.raises(QuizGenerationError, match="does not match any option"):
            generate_quiz_from_text("Some text")

    @patch("ai_utils._chat_completion")
    def test_coerces_a_numeric_string_correct_answer(self, mock_openai):
        question = _question("Q?")
        question["correct_answer"] = "2"
        mock_openai.return_value = json.dumps([question])

        result = generate_quiz_from_text("Some text", num_questions=1)

        assert result.questions[0]["correct_answer"] == 2


class TestQuestionExplanation:
    def test_selects_short_source_text_unchanged(self):
        text = "Paris is the capital of France."
        assert (
            select_explanation_context(text, "What is the capital of France?") == text
        )

    def test_returns_nothing_for_blank_source_text(self):
        assert select_explanation_context("   ", "A question?") == ""

    def test_prefers_passages_that_overlap_the_question(self):
        filler = "The history of ancient pottery spans many centuries of craft. " * 80
        relevant = "The mitochondria is the powerhouse of the cell and produces ATP."
        context = select_explanation_context(
            filler + relevant + filler,
            "What does the mitochondria produce?",
            ["ATP", "DNA", "Glucose", "Oxygen"],
        )

        assert "mitochondria" in context.lower()
        assert "ATP" in context

    def test_falls_back_to_the_start_when_nothing_overlaps(self):
        filler = "The history of ancient pottery spans many centuries of craft. " * 80
        context = select_explanation_context(
            filler,
            "What is photosynthesis?",
            ["Light", "Water", "Soil", "Wind"],
            limit=400,
        )

        assert context.startswith("The history of ancient pottery")
        assert len(context) <= 400

    @patch("ai_utils._chat_completion")
    def test_sends_the_question_and_source_without_a_quiz_schema(self, mock_complete):
        mock_complete.return_value = "Paris is the capital of France."

        result = explain_quiz_question(
            question="What is the capital of France?",
            options=["Berlin", "Paris", "London", "Madrid"],
            correct_answer=1,
            selected_answer=0,
            source_text="France is a country in Europe. Paris is its capital.",
            topic="Geography",
        )

        assert result == "Paris is the capital of France."
        prompt = mock_complete.call_args.args[0]
        kwargs = mock_complete.call_args.kwargs
        assert kwargs["constrain_to_quiz_schema"] is False
        assert kwargs["error_cls"] is ExplanationError
        assert "What is the capital of France?" in prompt
        assert "incorrect" in prompt
        assert "Paris is its capital" in prompt
        assert "Geography" in prompt

    @patch("ai_utils.OpenAI")
    def test_omits_the_quiz_schema_on_the_api_call(self, mock_openai_class):
        client = mock_openai_class.return_value
        message = MagicMock(content="Paris is the capital of France.")
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=message)]
        )

        explain_quiz_question(
            question="What is the capital of France?",
            options=["Berlin", "Paris", "London", "Madrid"],
            correct_answer=1,
            selected_answer=1,
        )

        kwargs = client.chat.completions.create.call_args.kwargs
        assert "response_format" not in kwargs
        assert kwargs["temperature"] == 0.3
        assert "study tutor" in kwargs["messages"][0]["content"].lower()

    @patch("ai_utils._chat_completion")
    def test_wraps_unexpected_failures(self, mock_complete):
        mock_complete.side_effect = RuntimeError("timeout")

        with pytest.raises(ExplanationError, match="Could not generate an explanation"):
            explain_quiz_question(
                question="What is 2+2?",
                options=["3", "4", "5", "6"],
                correct_answer=1,
            )
