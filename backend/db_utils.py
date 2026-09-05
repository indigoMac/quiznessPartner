from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from db import get_session_local
from models.question import Question
from models.quiz import Quiz
from models.result import Result


def get_db():
    """Get database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_quiz(
    db: Session, title: str, topic: Optional[str] = None, user_id: Optional[int] = None
):
    """Create a new quiz in the database."""
    quiz = Quiz(title=title, topic=topic, user_id=user_id)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


def add_questions_to_quiz(db: Session, quiz_id: int, questions_data: list):
    """Add questions to a quiz."""
    questions = []
    for q_data in questions_data:
        question = Question(
            quiz_id=quiz_id,
            question_text=q_data["question"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
        )
        db.add(question)
        questions.append(question)

    db.commit()
    for question in questions:
        db.refresh(question)

    return questions


def get_quiz(db: Session, quiz_id: int):
    """Get a quiz by ID."""
    return db.query(Quiz).filter(Quiz.id == quiz_id).first()


def get_quiz_with_questions(db: Session, quiz_id: int):
    """Get a quiz by ID with its questions."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        questions_data = [
            {
                "id": q.id,
                "question": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
            }
            for q in questions
        ]
        return {
            "id": quiz.id,
            "title": quiz.title,
            "topic": quiz.topic,
            "questions": questions_data,
        }
    return None


def record_quiz_result(
    db: Session,
    quiz_id: int,
    score: int,
    total: int,
    answers: list,
    user_id: Optional[int] = None,
):
    """Record a quiz result in the database."""
    result = Result(quiz_id=quiz_id, user_id=user_id, answers=answers, score=score)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_user_quizzes(db: Session, user_id: int) -> Tuple[List[dict], int, int]:
    """Return quizzes owned by a user plus dashboard counts."""
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == user_id)
        .order_by(Quiz.id.desc())
        .all()
    )
    total_quizzes = len(quizzes)
    completed = (
        db.query(func.count(func.distinct(Result.quiz_id)))
        .filter(Result.user_id == user_id)
        .scalar()
        or 0
    )

    if not quizzes:
        return [], total_quizzes, completed

    quiz_ids = [quiz.id for quiz in quizzes]

    question_counts = dict(
        db.query(Question.quiz_id, func.count(Question.id))
        .filter(Question.quiz_id.in_(quiz_ids))
        .group_by(Question.quiz_id)
        .all()
    )
    attempt_rows = (
        db.query(
            Result.quiz_id,
            func.count(Result.id),
            func.max(Result.score),
        )
        .filter(Result.user_id == user_id, Result.quiz_id.in_(quiz_ids))
        .group_by(Result.quiz_id)
        .all()
    )
    attempt_map = {
        quiz_id: {"attempt_count": count, "best_score": best_score}
        for quiz_id, count, best_score in attempt_rows
    }

    summaries = []
    for quiz in quizzes:
        attempts = attempt_map.get(quiz.id, {"attempt_count": 0, "best_score": None})
        summaries.append(
            {
                "id": quiz.id,
                "title": quiz.title,
                "topic": quiz.topic,
                "created_at": quiz.created_at,
                "question_count": question_counts.get(quiz.id, 0),
                "attempt_count": attempts["attempt_count"],
                "best_score": attempts["best_score"],
            }
        )

    return summaries, total_quizzes, completed
