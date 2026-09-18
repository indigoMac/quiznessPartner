from unittest.mock import MagicMock, patch

import pytest

from db_utils import create_quiz, create_study_topic
from services.explanation_service import (
    InvalidSelectionError,
    QuestionNotFoundError,
    QuizNotFoundError,
    generate_question_explanation,
)
from services.retrieval_service import RetrievalError
from tests.fixtures.factories import QuestionFactory, UserFactory


def _geography_question(db_session, source_text="Paris is the capital of France."):
    user = UserFactory.create(db_session)
    topic = create_study_topic(
        db_session,
        user_id=user.id,
        title="Geography",
        topic="Geography",
        source_text=source_text,
    )
    quiz = create_quiz(
        db_session,
        title="Capitals",
        topic="Geography",
        user_id=user.id,
        study_topic_id=topic.id,
    )
    question = QuestionFactory.create(
        db_session,
        quiz=quiz,
        question_text="What is the capital of France?",
        options=["London", "Paris", "Berlin", "Madrid"],
        correct_answer=1,
    )
    db_session.commit()
    return quiz, question


class TestGenerateQuestionExplanation:
    def test_missing_quiz(self, db_session):
        with pytest.raises(QuizNotFoundError):
            generate_question_explanation(db_session, 999, 1)

    def test_missing_question(self, db_session):
        user = UserFactory.create(db_session)
        quiz = create_quiz(db_session, "Title", "Topic", user.id)
        db_session.commit()

        with pytest.raises(QuestionNotFoundError):
            generate_question_explanation(db_session, quiz.id, 999)

    def test_rejects_an_invalid_selected_answer(self, db_session):
        quiz, question = _geography_question(db_session)

        with pytest.raises(InvalidSelectionError):
            generate_question_explanation(
                db_session, quiz.id, question.id, selected_answer=9
            )

    @patch("services.explanation_service.explain_quiz_question")
    def test_uses_stored_source_text(self, mock_explain, db_session):
        mock_explain.return_value = "Because the source says Paris."
        quiz, question = _geography_question(db_session)

        result = generate_question_explanation(
            db_session, quiz.id, question.id, selected_answer=0
        )

        assert result == "Because the source says Paris."
        kwargs = mock_explain.call_args.kwargs
        assert kwargs["question"] == "What is the capital of France?"
        assert kwargs["options"] == ["London", "Paris", "Berlin", "Madrid"]
        assert kwargs["correct_answer"] == 1
        assert kwargs["selected_answer"] == 0
        assert kwargs["source_text"] == "Paris is the capital of France."
        assert kwargs["topic"] == "Geography"

    @patch("services.explanation_service.explain_quiz_question")
    def test_explains_quizzes_without_source_material(self, mock_explain, db_session):
        mock_explain.return_value = "From the question alone."
        user = UserFactory.create(db_session)
        quiz = create_quiz(db_session, "Title", "Topic", user.id)
        question = QuestionFactory.create(
            db_session,
            quiz=quiz,
            question_text="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer=1,
        )
        db_session.commit()

        generate_question_explanation(
            db_session, quiz.id, question.id, selected_answer=1
        )

        assert mock_explain.call_args.kwargs["source_text"] == ""

    @patch("services.explanation_service.retrieval_enabled", return_value=True)
    @patch("services.explanation_service.search_study_topic")
    @patch("services.explanation_service.explain_quiz_question")
    def test_prefers_retrieved_passages(
        self, mock_explain, mock_search, _enabled, db_session
    ):
        mock_explain.return_value = "Grounded explanation."
        mock_search.return_value = [
            MagicMock(content="A retrieved passage about Paris.")
        ]
        quiz, question = _geography_question(db_session)

        generate_question_explanation(db_session, quiz.id, question.id)

        kwargs = mock_explain.call_args.kwargs
        assert kwargs["source_text"] == "A retrieved passage about Paris."
        mock_search.assert_called_once()

    @patch("services.explanation_service.retrieval_enabled", return_value=True)
    @patch("services.explanation_service.search_study_topic")
    @patch("services.explanation_service.explain_quiz_question")
    def test_falls_back_when_retrieval_fails(
        self, mock_explain, mock_search, _enabled, db_session
    ):
        mock_explain.return_value = "Fallback explanation."
        mock_search.side_effect = RetrievalError("no embeddings")
        quiz, question = _geography_question(db_session)

        generate_question_explanation(db_session, quiz.id, question.id)

        assert mock_explain.call_args.kwargs["source_text"] == (
            "Paris is the capital of France."
        )
