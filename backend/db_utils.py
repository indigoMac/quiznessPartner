from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from db import get_session_local
from models.question import Question
from models.quiz import Quiz
from models.result import Result
from models.study_topic import StudyTopic


def get_db():
    """Get database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_quiz(
    db: Session,
    title: str,
    topic: Optional[str] = None,
    user_id: Optional[int] = None,
    study_topic_id: Optional[int] = None,
):
    """Create a new quiz in the database."""
    quiz = Quiz(
        title=title,
        topic=topic,
        user_id=user_id,
        study_topic_id=study_topic_id,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


def create_study_topic(
    db: Session,
    user_id: int,
    title: str,
    topic: Optional[str] = None,
    source_text: Optional[str] = None,
    source_url: Optional[str] = None,
) -> StudyTopic:
    """Create a study topic that can hold multiple quizzes."""
    study_topic = StudyTopic(
        user_id=user_id,
        title=title,
        topic=topic,
        source_text=source_text,
        source_url=source_url,
    )
    db.add(study_topic)
    db.commit()
    db.refresh(study_topic)
    return study_topic


def get_study_topic_for_user(
    db: Session, study_topic_id: int, user_id: int
) -> Optional[StudyTopic]:
    """Get a study topic owned by the current user."""
    return (
        db.query(StudyTopic)
        .filter(StudyTopic.id == study_topic_id, StudyTopic.user_id == user_id)
        .first()
    )


def list_study_topic_questions(db: Session, study_topic_id: int) -> list:
    """Return previous questions in a study topic so new quizzes can avoid them."""
    quiz_ids = [
        quiz_id
        for (quiz_id,) in db.query(Quiz.id)
        .filter(Quiz.study_topic_id == study_topic_id)
        .all()
    ]
    if not quiz_ids:
        return []

    questions = db.query(Question).filter(Question.quiz_id.in_(quiz_ids)).all()
    return [
        {
            "question": question.question_text,
            "options": question.options,
            "correct_answer": question.correct_answer,
        }
        for question in questions
    ]


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
            "study_topic_id": quiz.study_topic_id,
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
                "study_topic_id": quiz.study_topic_id,
            }
        )

    return summaries, total_quizzes, completed


def list_user_study_topics(db: Session, user_id: int) -> List[dict]:
    """Group a user's quizzes into study topics for the dashboard."""
    quizzes, _, _ = list_user_quizzes(db, user_id)
    topics = (
        db.query(StudyTopic)
        .filter(StudyTopic.user_id == user_id)
        .order_by(StudyTopic.id.desc())
        .all()
    )
    grouped = {topic.id: [] for topic in topics}
    ungrouped = []
    for quiz in quizzes:
        if quiz["study_topic_id"] in grouped:
            grouped[quiz["study_topic_id"]].append(quiz)
        else:
            ungrouped.append(quiz)

    summaries = []
    for topic in topics:
        topic_quizzes = grouped.get(topic.id, [])
        if not topic_quizzes:
            continue
        completed_in_topic = sum(
            1 for quiz in topic_quizzes if quiz["attempt_count"] > 0
        )
        summaries.append(
            {
                "id": topic.id,
                "title": topic.title,
                "topic": topic.topic,
                "source_url": topic.source_url,
                "can_practice": bool(
                    (topic.source_text and topic.source_text.strip()) or topic.topic
                ),
                "quiz_count": len(topic_quizzes),
                "completed": completed_in_topic,
                "quizzes": topic_quizzes,
            }
        )

    if ungrouped:
        summaries.append(
            {
                "id": None,
                "title": "Other quizzes",
                "topic": None,
                "source_url": None,
                "can_practice": False,
                "quiz_count": len(ungrouped),
                "completed": sum(1 for quiz in ungrouped if quiz["attempt_count"] > 0),
                "quizzes": ungrouped,
            }
        )

    return summaries
