from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from db import get_session_local
from models.episode import AUDIO_NONE, EPISODE_FAILED, EPISODE_READY, Episode
from models.question import Question
from models.quiz import DEFAULT_QUIZ_DIFFICULTY, Quiz
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
    difficulty: str = DEFAULT_QUIZ_DIFFICULTY,
):
    """Create a new quiz in the database."""
    quiz = Quiz(
        title=title,
        topic=topic,
        user_id=user_id,
        study_topic_id=study_topic_id,
        difficulty=difficulty or DEFAULT_QUIZ_DIFFICULTY,
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


def get_study_topic(db: Session, study_topic_id: int) -> Optional[StudyTopic]:
    """Get a study topic by ID."""
    return db.query(StudyTopic).filter(StudyTopic.id == study_topic_id).first()


def get_study_topic_for_user(
    db: Session, study_topic_id: int, user_id: int
) -> Optional[StudyTopic]:
    """Get a study topic owned by the current user."""
    return (
        db.query(StudyTopic)
        .filter(StudyTopic.id == study_topic_id, StudyTopic.user_id == user_id)
        .first()
    )


def get_episode_for_study_topic(
    db: Session, study_topic_id: int, user_id: int
) -> Optional[Episode]:
    """Return the episode for a study topic when the caller owns it."""
    return (
        db.query(Episode)
        .filter(
            Episode.study_topic_id == study_topic_id,
            Episode.user_id == user_id,
        )
        .first()
    )


def save_episode(
    db: Session,
    study_topic: StudyTopic,
    status: str,
    title: Optional[str] = None,
    script: Optional[list] = None,
    error_message: Optional[str] = None,
) -> Episode:
    """Create or replace the single episode for a study topic.

    A script is stored only when status is ready. A failure stores the
    error and clears any previous script. Replacing the script clears audio,
    because the old file would no longer match the new lines.
    """
    episode = db.query(Episode).filter(Episode.study_topic_id == study_topic.id).first()
    if episode is None:
        episode = Episode(
            study_topic_id=study_topic.id,
            user_id=study_topic.user_id,
            audio_status=AUDIO_NONE,
        )
        db.add(episode)

    episode.user_id = study_topic.user_id
    episode.status = status
    # A new script no longer matches any audio already generated for this row.
    episode.audio_status = AUDIO_NONE
    episode.audio_error = None
    episode.duration_seconds = None
    episode.segment_timings = None
    episode.audio_key = None
    if status == EPISODE_READY:
        episode.title = title
        episode.script = script
        episode.error_message = None
    elif status == EPISODE_FAILED:
        episode.title = None
        episode.script = None
        episode.error_message = error_message
    else:
        episode.title = None
        episode.script = None
        episode.error_message = None
    db.commit()
    db.refresh(episode)
    return episode


def get_quiz_question(
    db: Session, quiz_id: int, question_id: int
) -> Optional[Question]:
    """Get a question that belongs to a specific quiz."""
    return (
        db.query(Question)
        .filter(Question.id == question_id, Question.quiz_id == quiz_id)
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
            "difficulty": quiz.difficulty or DEFAULT_QUIZ_DIFFICULTY,
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
        db.query(Quiz).filter(Quiz.user_id == user_id).order_by(Quiz.id.desc()).all()
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
                "difficulty": quiz.difficulty or DEFAULT_QUIZ_DIFFICULTY,
            }
        )

    return summaries, total_quizzes, completed


def _source_label(topic: StudyTopic) -> Optional[str]:
    """Short description of where a topic's material came from."""
    if topic.source_url:
        return topic.source_url
    if topic.source_text and topic.source_text.strip():
        return "Saved text"
    return None


def list_user_study_topics(db: Session, user_id: int) -> List[dict]:
    """Group a user's quizzes into study topics for the dashboard.

    A topic saved without a quiz still appears when it has source text.
    """
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
        has_source = bool(topic.source_text and topic.source_text.strip())
        if not topic_quizzes and not has_source:
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
                "source_label": _source_label(topic),
                "can_practice": bool(has_source or topic.topic),
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
                "source_label": None,
                "can_practice": False,
                "quiz_count": len(ungrouped),
                "completed": sum(1 for quiz in ungrouped if quiz["attempt_count"] > 0),
                "quizzes": ungrouped,
            }
        )

    return summaries
