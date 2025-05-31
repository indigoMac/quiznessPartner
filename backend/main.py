import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy.orm import Session

from ai_utils import extract_text_from_pdf, generate_quiz_from_text
from auth import auth_router
from auth.dependencies import get_optional_user
# Import utility modules
from db_utils import (
    add_questions_to_quiz,
    create_quiz,
    get_db,
    get_quiz_with_questions,
    record_quiz_result,
)
from models.user import User

# Load environment variables
load_dotenv()


class AuthSettings(BaseSettings):
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )


# Initialize FastAPI app
app = FastAPI(
    title="QuizNess API",
    description="AI-powered quiz generation platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router, prefix="/api/v1")


# Pydantic models for request/response
class QuizRequest(BaseModel):
    content: str
    topic: str
    num_questions: int = 5


class AnswerSubmission(BaseModel):
    quiz_id: int
    answers: List[int]


class QuizResponse(BaseModel):
    id: str
    title: str
    topic: str
    questions: List[Dict[str, Any]]


class ResultResponse(BaseModel):
    quiz_id: int
    score: int
    total: int
    answers: List[int]


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
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Generate a quiz from text content"""
    try:
        # Generate quiz using AI
        questions_data = generate_quiz_from_text(
            request.content, request.topic, request.num_questions
        )

        if not questions_data:
            raise HTTPException(
                status_code=500, detail="Failed to generate quiz questions"
            )

        # Create quiz in database
        quiz_title = f"Quiz on {request.topic}"
        user_id = current_user.id if current_user else None
        quiz = create_quiz(db, quiz_title, request.topic, user_id)

        # Add questions to quiz
        add_questions_to_quiz(db, quiz.id, questions_data)

        # Get the complete quiz with questions
        complete_quiz = get_quiz_with_questions(db, quiz.id)

        return QuizResponse(
            id=str(complete_quiz["id"]),
            title=complete_quiz["title"],
            topic=complete_quiz["topic"],
            questions=complete_quiz["questions"],
        )

    except Exception as e:
        print(f"Error in generate_quiz: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/upload-document", response_model=QuizResponse)
async def upload_document(
    file: UploadFile = File(...),
    topic: str = Form(...),
    num_questions: int = Form(5),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Upload a document and generate a quiz from it"""
    try:
        # Validate file type
        if not file.filename.lower().endswith((".pdf", ".txt")):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported",
            )

        # Extract text from file
        if file.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file.file)
        else:
            # Handle text files
            content = await file.read()
            text = content.decode("utf-8")

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file",
            )

        # Generate quiz using AI
        questions_data = generate_quiz_from_text(text, topic, num_questions)

        if not questions_data:
            raise HTTPException(
                status_code=500, detail="Failed to generate quiz questions"
            )

        # Create quiz in database
        quiz_title = f"Quiz on {topic}"
        user_id = current_user.id if current_user else None
        quiz = create_quiz(db, quiz_title, topic, user_id)

        # Add questions to quiz
        add_questions_to_quiz(db, quiz.id, questions_data)

        # Get the complete quiz with questions
        complete_quiz = get_quiz_with_questions(db, quiz.id)

        return QuizResponse(
            id=str(complete_quiz["id"]),
            title=complete_quiz["title"],
            topic=complete_quiz["topic"],
            questions=complete_quiz["questions"],
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in upload_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/quiz/{quiz_id}")
async def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Get a quiz by ID"""
    try:
        quiz = get_quiz_with_questions(db, quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        return quiz
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_quiz: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/submit-answer", response_model=ResultResponse)
async def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    """Submit answers for a quiz"""
    try:
        # Get the quiz to validate answers
        quiz = get_quiz_with_questions(db, submission.quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        questions = quiz["questions"]
        if len(submission.answers) != len(questions):
            raise HTTPException(
                status_code=400,
                detail="Number of answers doesn't match number of questions",
            )

        # Calculate score
        score = 0
        for i, answer in enumerate(submission.answers):
            if answer == questions[i]["correct_answer"]:
                score += 1

        # Record the result
        record_quiz_result(
            db, submission.quiz_id, score, len(questions), submission.answers
        )

        return ResultResponse(
            quiz_id=submission.quiz_id,
            score=score,
            total=len(questions),
            answers=submission.answers,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in submit_answer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
