from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import uuid
from pydantic_settings import BaseSettings

# Import utility modules
from db_utils import get_db, create_quiz, add_questions_to_quiz, get_quiz_with_questions, record_quiz_result
from ai_utils import extract_text_from_pdf, generate_quiz_from_text
from auth import auth_router
from models.user import User
from auth.dependencies import get_current_active_user, get_optional_user

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: List[str] = ["http://localhost:3000"]
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Quizness Partner API",
    description="AI-powered quiz generation API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# Include authentication router
app.include_router(auth_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "healthy", "version": "1.0.0"},
        status_code=200
    )

# Basic models for API
class QuizRequest(BaseModel):
    content: str
    topic: Optional[str] = None
    num_questions: Optional[int] = 5

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int

class QuizResponse(BaseModel):
    id: str
    questions: List[Dict[str, Any]]
    topic: Optional[str] = None

class AnswerSubmission(BaseModel):
    quiz_id: int
    answers: List[int]  # List of selected answer indices

class QuizResult(BaseModel):
    quiz_id: int
    score: int
    total: int
    answers: List[int]
    correct_answers: List[int]

# Document upload endpoint
@app.post("/api/v1/upload-document", response_model=QuizResponse)
async def upload_document(
    file: UploadFile = File(...),
    topic: Optional[str] = Form(None),
    num_questions: Optional[int] = Form(5),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    try:
        # Extract text from PDF
        if file.content_type == "application/pdf":
            content = extract_text_from_pdf(file.file)
        else:
            # For other file types (assuming text)
            content = (await file.read()).decode("utf-8")
        
        # Generate quiz questions using AI
        questions = generate_quiz_from_text(content, topic, num_questions)
        
        # Store quiz and questions in database
        title = f"Quiz on {topic}" if topic else f"Quiz from {file.filename}"
        user_id = current_user.id if current_user else None
        quiz = create_quiz(db, title=title, topic=topic, user_id=user_id)
        add_questions_to_quiz(db, quiz.id, questions)
        
        return {
            "id": str(quiz.id),
            "questions": questions,
            "topic": topic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

# Quiz generation endpoint
@app.post("/api/v1/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    try:
        # Generate quiz questions using AI
        questions = generate_quiz_from_text(
            request.content,
            request.topic,
            request.num_questions
        )
        
        # Store quiz and questions in database
        title = f"Quiz on {request.topic}" if request.topic else "Custom Quiz"
        user_id = current_user.id if current_user else None
        quiz = create_quiz(db, title=title, topic=request.topic, user_id=user_id)
        add_questions_to_quiz(db, quiz.id, questions)
        
        return {
            "id": str(quiz.id),
            "questions": questions,
            "topic": request.topic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

# Get quiz by ID
@app.get("/api/v1/quiz/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz, questions = get_quiz_with_questions(db, quiz_id)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    print(f"Raw quiz data: {quiz.__dict__}")
    print(f"Raw questions data: {[q.__dict__ for q in questions]}")
    
    # Convert DB models to API response format
    questions_data = [
        {
            "id": q.id,
            "question": q.question_text,
            "options": q.options,
            "correct_answer": q.correct_answer
        } for q in questions
    ]
    
    response_data = {
        "id": str(quiz.id),
        "title": quiz.title,
        "questions": questions_data,
        "topic": quiz.topic
    }
    
    print(f"Final response data: {response_data}")
    
    return response_data

# Submit quiz answers and get results
@app.post("/api/v1/submit-answer", response_model=QuizResult)
async def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    quiz, questions = get_quiz_with_questions(db, submission.quiz_id)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    correct_answers = [q.correct_answer for q in questions]
    score = sum(1 for a, c in zip(submission.answers, correct_answers) if a == c)
    
    # Record the result in the database
    record_quiz_result(
        db, 
        quiz_id=submission.quiz_id,
        answers=submission.answers,
        score=score
    )
    
    return {
        "quiz_id": submission.quiz_id,
        "score": score,
        "total": len(questions),
        "answers": submission.answers,
        "correct_answers": correct_answers
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    ) 