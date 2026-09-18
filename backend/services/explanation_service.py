"""On-demand explanations for quiz questions, grounded in source material."""

import logging
from typing import List, Optional, Sequence

from sqlalchemy.orm import Session

from ai_utils import explain_quiz_question, select_explanation_context
from db_utils import get_quiz, get_quiz_question, get_study_topic
from services.retrieval_service import (
    RetrievalError,
    retrieval_enabled,
    search_study_topic,
)

logger = logging.getLogger(__name__)

MAX_RETRIEVED_PASSAGES = 3


class QuizNotFoundError(Exception):
    """Raised when an explanation is requested for a quiz that does not exist."""


class QuestionNotFoundError(Exception):
    """Raised when an explanation is requested for a missing quiz question."""


class InvalidSelectionError(ValueError):
    """Raised when selected_answer is not one of the question's options."""


def _source_context(
    db: Session,
    study_topic_id: Optional[int],
    question: str,
    options: Sequence[str],
) -> str:
    if not study_topic_id:
        return ""

    topic = get_study_topic(db, study_topic_id)
    source_text = (topic.source_text or "").strip() if topic else ""

    if retrieval_enabled():
        try:
            passages = search_study_topic(
                db, study_topic_id, question, limit=MAX_RETRIEVED_PASSAGES
            )
            combined = "\n\n".join(item.content for item in passages if item.content)
            if combined.strip():
                return combined.strip()
        except RetrievalError:
            logger.warning(
                "Retrieval failed for study topic %s; using stored source text",
                study_topic_id,
            )

    return select_explanation_context(source_text, question, list(options))


def generate_question_explanation(
    db: Session,
    quiz_id: int,
    question_id: int,
    selected_answer: Optional[int] = None,
) -> str:
    """Load a question and generate a grounded explanation of it."""
    quiz = get_quiz(db, quiz_id)
    if not quiz:
        raise QuizNotFoundError()

    question = get_quiz_question(db, quiz_id, question_id)
    if not question:
        raise QuestionNotFoundError()

    options: List[str] = list(question.options or [])
    if selected_answer is not None and not 0 <= selected_answer < len(options):
        raise InvalidSelectionError(
            "Selected answer is not a valid option for this question."
        )

    source_text = _source_context(
        db, quiz.study_topic_id, question.question_text, options
    )
    return explain_quiz_question(
        question=question.question_text,
        options=options,
        correct_answer=question.correct_answer,
        selected_answer=selected_answer,
        source_text=source_text,
        topic=quiz.topic,
    )
