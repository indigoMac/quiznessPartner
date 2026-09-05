import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai_utils import QuizGenerationError, extract_text_from_pdf, generate_quiz_from_text
from auth import auth_router
from auth.dependencies import get_current_active_user, get_optional_user
from db_utils import (
    add_questions_to_quiz,
    create_quiz,
    get_db,
    get_quiz_with_questions,
    list_user_quizzes,
    record_quiz_result,
)
from models.user import User

load_dotenv()


def _cors_origins() -> List[str]:
    raw = os.getenv("BACKEND_CORS_ORIGINS", '["http://localhost:3000"]')
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and parsed:
            return [str(origin) for origin in parsed]
    except json.JSONDecodeError:
        pass
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:3000"]


app = FastAPI(
    title="QuizNess API",
    description="AI-powered quiz generation platform",
    version="1.0.0",
)

cors_origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


class QuizRequest(BaseModel):
    content: str
    topic: Optional[str] = None
    num_questions: int = 5


class AnswerSubmission(BaseModel):
    quiz_id: int
    answers: List[int]


class QuizResponse(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    questions: List[Dict[str, Any]]


class ResultResponse(BaseModel):
    quiz_id: int
    score: int
    total: int
    answers: List[int]


class QuizSummary(BaseModel):
    id: int
    title: str
    topic: Optional[str] = None
    created_at: Optional[str] = None
    question_count: int
    attempt_count: int
    best_score: Optional[int] = None


class QuizListResponse(BaseModel):
    quizzes: List[QuizSummary]
    total_quizzes: int
    completed: int


def _quiz_title(topic: Optional[str]) -> str:
    return f"Quiz on {topic}" if topic else "Untitled Quiz"


def _serialize_created_at(value) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to QuizNess API"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "QuizNess API is running"}


@app.post("/api/v1/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a quiz from text content. Requires a logged-in user."""
    try:
        questions_data = generate_quiz_from_text(
            request.content, request.topic, request.num_questions
        )

        quiz = create_quiz(
            db, _quiz_title(request.topic), request.topic, current_user.id
        )
        add_questions_to_quiz(db, quiz.id, questions_data)
        complete_quiz = get_quiz_with_questions(db, quiz.id)

        return QuizResponse(
            id=str(complete_quiz["id"]),
            title=complete_quiz["title"],
            topic=complete_quiz["topic"],
            questions=complete_quiz["questions"],
        )
    except QuizGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/api/v1/upload-document", response_model=QuizResponse)
async def upload_document(
    file: UploadFile = File(...),
    topic: Optional[str] = Form(None),
    num_questions: int = Form(5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a PDF or text file and generate a quiz from it."""
    try:
        if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported",
            )

        if file.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file.file)
        else:
            content = await file.read()
            text = content.decode("utf-8")

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file",
            )

        questions_data = generate_quiz_from_text(text, topic, num_questions)
        quiz = create_quiz(db, _quiz_title(topic), topic, current_user.id)
        add_questions_to_quiz(db, quiz.id, questions_data)
        complete_quiz = get_quiz_with_questions(db, quiz.id)

        return QuizResponse(
            id=str(complete_quiz["id"]),
            title=complete_quiz["title"],
            topic=complete_quiz["topic"],
            questions=complete_quiz["questions"],
        )
    except QuizGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/api/v1/quizzes", response_model=QuizListResponse)
async def list_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List quizzes created by the current user."""
    quizzes, total_quizzes, completed = list_user_quizzes(db, current_user.id)
    return QuizListResponse(
        quizzes=[
            QuizSummary(
                id=item["id"],
                title=item["title"],
                topic=item["topic"],
                created_at=_serialize_created_at(item["created_at"]),
                question_count=item["question_count"],
                attempt_count=item["attempt_count"],
                best_score=item["best_score"],
            )
            for item in quizzes
        ],
        total_quizzes=total_quizzes,
        completed=completed,
    )


@app.get("/api/v1/quiz/{quiz_id}")
async def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Get a quiz by ID. Public so a quiz link can be shared."""
    try:
        quiz = get_quiz_with_questions(db, quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return quiz
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/api/v1/submit-answer", response_model=ResultResponse)
async def submit_answer(
    submission: AnswerSubmission,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Submit answers for a quiz. Records the user when logged in."""
    try:
        quiz = get_quiz_with_questions(db, submission.quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        questions = quiz["questions"]
        if len(submission.answers) != len(questions):
            raise HTTPException(
                status_code=400,
                detail="Number of answers doesn't match number of questions",
            )

        score = 0
        for i, answer in enumerate(submission.answers):
            if answer == questions[i]["correct_answer"]:
                score += 1

        record_quiz_result(
            db,
            submission.quiz_id,
            score,
            len(questions),
            submission.answers,
            current_user.id if current_user else None,
        )

        return ResultResponse(
            quiz_id=submission.quiz_id,
            score=score,
            total=len(questions),
            answers=submission.answers,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


if __name__ == "__main__":
    import uvicorn

    # Binding to all interfaces is intentional for Docker deployment
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
