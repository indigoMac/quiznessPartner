from sqlalchemy.orm import Session

from db import SessionLocal
from models.question import Question
from models.quiz import Quiz
from models.result import Result


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_quiz(db: Session, title: str, topic: str = None, user_id: int = None):
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
    """Get a quiz by ID with its questions."""
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
    user_id: int = None,
):
    """Record a quiz result in the database."""
    result = Result(quiz_id=quiz_id, user_id=user_id, answers=answers, score=score)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
