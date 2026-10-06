import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_utils import (
    DEFAULT_QUIZ_DIFFICULTY,
    EpisodeGenerationError,
    ExplanationError,
    QuizDifficulty,
    QuizGenerationError,
    as_generated_quiz,
    extract_text_from_pdf,
    generate_episode_script,
    generate_quiz_from_text,
    source_text_for_storage,
)
from auth import auth_router
from auth.dependencies import get_current_active_user, get_optional_user
from db_utils import (
    add_questions_to_quiz,
    create_quiz,
    create_study_topic,
    get_db,
    get_episode_for_study_topic,
    get_quiz_with_questions,
    get_study_topic_for_user,
    list_study_topic_questions,
    list_user_quizzes,
    list_user_study_topics,
    record_quiz_result,
    save_episode,
)
from env_loader import load_app_env
from models.episode import (
    AUDIO_FAILED,
    AUDIO_NONE,
    AUDIO_READY,
    EPISODE_FAILED,
    EPISODE_PENDING,
    EPISODE_READY,
)
from models.user import User
from services.episode_audio import (
    AUDIO_JOB_STARTED,
    begin_episode_audio,
    synthesize_episode_audio,
)
from services.episode_storage import (
    AudioStorageError,
    delete_stored_audio,
    get_episode_storage,
)
from services.explanation_service import (
    InvalidSelectionError,
    QuestionNotFoundError,
    QuizNotFoundError,
    generate_question_explanation,
)
from services.retrieval_service import (
    RetrievalError,
    index_study_topic,
    retrieval_enabled,
)
from url_utils import UrlFetchError, fetch_url_text

logger = logging.getLogger(__name__)

load_app_env()

if os.getenv("ENVIRONMENT") == "production":
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key or secret_key == "your-secret-key-here":
        raise RuntimeError("SECRET_KEY must be set to a strong value in production")


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
cors_origin_regex = os.getenv("BACKEND_CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


class QuizRequest(BaseModel):
    content: str
    topic: Optional[str] = None
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: QuizDifficulty = DEFAULT_QUIZ_DIFFICULTY


class UrlQuizRequest(BaseModel):
    url: str
    topic: Optional[str] = None
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: QuizDifficulty = DEFAULT_QUIZ_DIFFICULTY


class PracticeRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: QuizDifficulty = DEFAULT_QUIZ_DIFFICULTY


class AnswerSubmission(BaseModel):
    quiz_id: int
    answers: List[int]


class QuizResponse(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    study_topic_id: Optional[int] = None
    questions: List[Dict[str, Any]]
    difficulty: str = DEFAULT_QUIZ_DIFFICULTY
    # How many were asked for. Source material sometimes cannot support the
    # full request, so clients compare this against len(questions) to tell
    # the user they got fewer. Not persisted; it describes the request.
    requested_questions: Optional[int] = None


class ResultResponse(BaseModel):
    quiz_id: int
    score: int
    total: int
    answers: List[int]


class ExplainRequest(BaseModel):
    selected_answer: Optional[int] = Field(default=None, ge=0)


class ExplainResponse(BaseModel):
    explanation: str


class QuizSummary(BaseModel):
    id: int
    title: str
    topic: Optional[str] = None
    created_at: Optional[str] = None
    question_count: int
    attempt_count: int
    best_score: Optional[int] = None
    study_topic_id: Optional[int] = None
    difficulty: str = DEFAULT_QUIZ_DIFFICULTY


class StudyTopicSummary(BaseModel):
    id: Optional[int] = None
    title: str
    topic: Optional[str] = None
    source_url: Optional[str] = None
    source_label: Optional[str] = None
    can_practice: bool
    quiz_count: int
    completed: int
    quizzes: List[QuizSummary]


class StudyTopicResponse(BaseModel):
    id: int
    title: str
    topic: Optional[str] = None
    source_url: Optional[str] = None
    can_practice: bool


class EpisodeSegmentResponse(BaseModel):
    chapter: str
    speaker: str
    text: str


class SegmentTimingResponse(BaseModel):
    start: float
    end: float


class EpisodeResponse(BaseModel):
    id: int
    study_topic_id: int
    status: str
    title: Optional[str] = None
    script: Optional[List[EpisodeSegmentResponse]] = None
    error_message: Optional[str] = None
    audio_status: str = AUDIO_NONE
    audio_error: Optional[str] = None
    duration_seconds: Optional[float] = None
    segment_timings: Optional[List[SegmentTimingResponse]] = None


class QuizListResponse(BaseModel):
    quizzes: List[QuizSummary]
    study_topics: List[StudyTopicSummary]
    total_quizzes: int
    completed: int
    total_topics: int


def _optional_label(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _study_topic_title(
    requested_topic: Optional[str],
    page_title: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    return requested_topic or page_title or filename or "Study topic"


def _can_practice_topic(study_topic) -> bool:
    source = study_topic.source_text or ""
    return bool(source.strip() or study_topic.topic)


def _study_topic_response(study_topic) -> "StudyTopicResponse":
    return StudyTopicResponse(
        id=study_topic.id,
        title=study_topic.title,
        topic=study_topic.topic,
        source_url=study_topic.source_url,
        can_practice=_can_practice_topic(study_topic),
    )


def _episode_response(episode) -> "EpisodeResponse":
    """Return a script only when the episode is ready."""
    script_ready = episode.status == EPISODE_READY
    audio_ready = episode.audio_status == AUDIO_READY
    return EpisodeResponse(
        id=episode.id,
        study_topic_id=episode.study_topic_id,
        status=episode.status,
        title=episode.title if script_ready else None,
        script=episode.script if script_ready else None,
        error_message=(
            episode.error_message if episode.status == EPISODE_FAILED else None
        ),
        audio_status=episode.audio_status or AUDIO_NONE,
        audio_error=(
            episode.audio_error if episode.audio_status == AUDIO_FAILED else None
        ),
        duration_seconds=episode.duration_seconds if audio_ready else None,
        segment_timings=episode.segment_timings if audio_ready else None,
    )


def _require_owned_topic(db: Session, study_topic_id: int, user_id: int):
    study_topic = get_study_topic_for_user(db, study_topic_id, user_id)
    if not study_topic:
        raise HTTPException(status_code=404, detail="Study topic not found")
    return study_topic


async def _text_from_upload(file: UploadFile) -> str:
    """Read a PDF or text upload, or raise the same errors as quiz upload."""
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported",
        )

    if file.filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file.file)
    else:
        raw = await file.read()
        text = raw.decode("utf-8")

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the file",
        )
    return text


def _store_study_material(
    db: Session,
    user_id: int,
    title: str,
    topic: Optional[str],
    source_text: str,
    source_url: Optional[str] = None,
):
    study_topic = create_study_topic(
        db,
        user_id=user_id,
        title=title,
        topic=topic,
        source_text=source_text_for_storage(source_text),
        source_url=source_url,
    )
    _index_source_material(db, study_topic.id, source_text)
    return study_topic


def _serialize_created_at(value) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def _index_source_material(
    db: Session, study_topic_id: int, source_text: Optional[str]
) -> None:
    """Index a new topic's material for retrieval, if that is switched on.

    A failure here is logged rather than raised: the quiz the user asked for
    has already been generated, and losing it because a secondary index could
    not be built would be the worse outcome.
    """
    if not source_text or not retrieval_enabled():
        return
    try:
        index_study_topic(db, study_topic_id, source_text)
    except RetrievalError:
        logger.exception("Could not index study topic %s", study_topic_id)


def _persist_generated_quiz(
    db: Session,
    generated,
    user_id: int,
    source_text: Optional[str] = None,
    source_url: Optional[str] = None,
    study_topic_id: Optional[int] = None,
    requested_questions: Optional[int] = None,
    difficulty: str = DEFAULT_QUIZ_DIFFICULTY,
) -> QuizResponse:
    if study_topic_id is not None:
        study_topic = get_study_topic_for_user(db, study_topic_id, user_id)
        if not study_topic:
            raise HTTPException(status_code=404, detail="Study topic not found")
    else:
        title = generated.topic or generated.title
        study_topic = create_study_topic(
            db,
            user_id=user_id,
            title=title or "Study topic",
            topic=generated.topic,
            source_text=source_text_for_storage(source_text or ""),
            source_url=source_url,
        )

        _index_source_material(db, study_topic.id, source_text)

    quiz = create_quiz(
        db,
        generated.title,
        generated.topic,
        user_id,
        study_topic.id,
        difficulty=difficulty,
    )
    add_questions_to_quiz(db, quiz.id, generated.questions)
    complete_quiz = get_quiz_with_questions(db, quiz.id)
    return QuizResponse(
        id=str(complete_quiz["id"]),
        title=complete_quiz["title"],
        topic=complete_quiz["topic"],
        study_topic_id=complete_quiz.get("study_topic_id"),
        questions=complete_quiz["questions"],
        difficulty=complete_quiz.get("difficulty") or difficulty,
        requested_questions=requested_questions,
    )


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
        generated = as_generated_quiz(
            generate_quiz_from_text(
                request.content,
                topic=request.topic,
                num_questions=request.num_questions,
                difficulty=request.difficulty,
            ),
            request.topic,
        )
        return _persist_generated_quiz(
            db,
            generated,
            current_user.id,
            source_text=request.content,
            requested_questions=request.num_questions,
            difficulty=request.difficulty,
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
    difficulty: QuizDifficulty = Form(DEFAULT_QUIZ_DIFFICULTY),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a PDF or text file and generate a quiz from it."""
    try:
        text = await _text_from_upload(file)
        generated = as_generated_quiz(
            generate_quiz_from_text(
                text,
                topic=topic,
                num_questions=num_questions,
                difficulty=difficulty,
            ),
            topic,
        )
        return _persist_generated_quiz(
            db,
            generated,
            current_user.id,
            source_text=text,
            requested_questions=num_questions,
            difficulty=difficulty,
        )
    except QuizGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/api/v1/study-topics", response_model=StudyTopicResponse)
async def create_study_material(
    file: Optional[UploadFile] = File(None),
    content: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Save a PDF, text, or public URL as a study topic without creating a quiz."""
    try:
        requested_topic = _optional_label(topic)
        cleaned_content = _optional_label(content)
        cleaned_url = _optional_label(url)
        has_file = file is not None and bool(file.filename)
        provided = sum(
            1
            for present in (has_file, bool(cleaned_content), bool(cleaned_url))
            if present
        )
        if provided != 1:
            raise HTTPException(
                status_code=400,
                detail="Provide a file, text, or a URL",
            )

        page_title = None
        filename = None
        source_url = None
        if file is not None and file.filename:
            text = await _text_from_upload(file)
            filename = file.filename
        elif cleaned_url:
            text, page_title = fetch_url_text(cleaned_url)
            source_url = cleaned_url
        else:
            text = cleaned_content or ""

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file",
            )

        study_topic = _store_study_material(
            db,
            current_user.id,
            title=_study_topic_title(requested_topic, page_title, filename),
            topic=requested_topic,
            source_text=text,
            source_url=source_url,
        )
        return _study_topic_response(study_topic)
    except UrlFetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/api/v1/study-topics/{study_topic_id}", response_model=StudyTopicResponse)
async def get_study_material(
    study_topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return one study topic owned by the current user."""
    study_topic = _require_owned_topic(db, study_topic_id, current_user.id)
    return _study_topic_response(study_topic)


@app.post(
    "/api/v1/study-topics/{study_topic_id}/episode",
    response_model=EpisodeResponse,
)
async def create_study_episode(
    study_topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate or replace the single episode script for a study topic.

    A model response that fails validation is stored as failed and returned
    with error_message. It is not stored as a ready script.
    """
    study_topic = _require_owned_topic(db, study_topic_id, current_user.id)
    source_text = (study_topic.source_text or "").strip()
    if not source_text:
        raise HTTPException(
            status_code=400,
            detail=(
                "This study topic does not have source text " "to turn into an episode."
            ),
        )

    existing = get_episode_for_study_topic(db, study_topic.id, current_user.id)
    if existing is not None:
        delete_stored_audio(existing.audio_key)
    save_episode(db, study_topic, EPISODE_PENDING)
    try:
        generated = generate_episode_script(
            source_text,
            study_topic.topic or study_topic.title,
        )
    except EpisodeGenerationError as exc:
        logger.warning(
            "Episode script for study topic %s failed: %s",
            study_topic.id,
            exc,
        )
        episode = save_episode(
            db,
            study_topic,
            EPISODE_FAILED,
            error_message=str(exc),
        )
        return _episode_response(episode)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Episode script generation failed for study topic %s",
            study_topic.id,
        )
        save_episode(
            db,
            study_topic,
            EPISODE_FAILED,
            error_message="Could not write the episode script. Please try again.",
        )
        raise HTTPException(
            status_code=500,
            detail="Could not write the episode script. Please try again.",
        ) from exc

    episode = save_episode(
        db,
        study_topic,
        EPISODE_READY,
        title=generated.title,
        script=generated.segments,
    )
    return _episode_response(episode)


@app.get(
    "/api/v1/study-topics/{study_topic_id}/episode",
    response_model=EpisodeResponse,
)
async def get_study_episode(
    study_topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the caller's episode. Anyone else, and a missing episode, is 404."""
    study_topic = _require_owned_topic(db, study_topic_id, current_user.id)
    episode = get_episode_for_study_topic(db, study_topic.id, current_user.id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return _episode_response(episode)


@app.post(
    "/api/v1/study-topics/{study_topic_id}/episode/audio",
    response_model=EpisodeResponse,
)
async def start_study_episode_audio(
    study_topic_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Start speech for a ready script and return before the file exists.

    A second request while a job is still inside the timeout returns the
    same episode and does not start another synthesis.
    """
    study_topic = _require_owned_topic(db, study_topic_id, current_user.id)
    episode = get_episode_for_study_topic(db, study_topic.id, current_user.id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if episode.status != EPISODE_READY or not episode.script:
        raise HTTPException(
            status_code=400,
            detail="The episode script is not ready for audio.",
        )

    outcome = begin_episode_audio(db, episode)
    if outcome == AUDIO_JOB_STARTED:
        background_tasks.add_task(synthesize_episode_audio, episode.id)
    return _episode_response(episode)


@app.get("/api/v1/study-topics/{study_topic_id}/episode/audio")
async def get_study_episode_audio(
    study_topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream the finished audio file to its owner."""
    study_topic = _require_owned_topic(db, study_topic_id, current_user.id)
    episode = get_episode_for_study_topic(db, study_topic.id, current_user.id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if episode.audio_status != AUDIO_READY or not _stored_audio_key(episode.audio_key):
        raise HTTPException(status_code=409, detail="Episode audio is not ready.")
    try:
        stream = get_episode_storage().stream(episode.audio_key)
    except (FileNotFoundError, AudioStorageError) as exc:
        raise HTTPException(
            status_code=404, detail="Episode audio was not found."
        ) from exc
    return StreamingResponse(stream, media_type="audio/wav")


def _stored_audio_key(key: Optional[str]) -> bool:
    return bool(key and key.startswith("episodes/"))


@app.post("/api/v1/generate-quiz-from-url", response_model=QuizResponse)
async def generate_quiz_from_url(
    request: UrlQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a quiz from a public web page or PDF URL."""
    try:
        text, page_title = fetch_url_text(request.url)
        topic = request.topic or page_title
        generated = as_generated_quiz(
            generate_quiz_from_text(
                text,
                topic=topic,
                num_questions=request.num_questions,
                difficulty=request.difficulty,
            ),
            topic,
        )
        return _persist_generated_quiz(
            db,
            generated,
            current_user.id,
            source_text=text,
            source_url=request.url,
            requested_questions=request.num_questions,
            difficulty=request.difficulty,
        )
    except UrlFetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
    """List quizzes created by the current user, grouped into study topics."""
    quizzes, total_quizzes, completed = list_user_quizzes(db, current_user.id)
    study_topics = list_user_study_topics(db, current_user.id)
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
                study_topic_id=item.get("study_topic_id"),
                difficulty=item.get("difficulty") or DEFAULT_QUIZ_DIFFICULTY,
            )
            for item in quizzes
        ],
        study_topics=[
            StudyTopicSummary(
                id=item["id"],
                title=item["title"],
                topic=item["topic"],
                source_url=item["source_url"],
                source_label=item.get("source_label"),
                can_practice=item["can_practice"],
                quiz_count=item["quiz_count"],
                completed=item["completed"],
                quizzes=[
                    QuizSummary(
                        id=quiz["id"],
                        title=quiz["title"],
                        topic=quiz["topic"],
                        created_at=_serialize_created_at(quiz["created_at"]),
                        question_count=quiz["question_count"],
                        attempt_count=quiz["attempt_count"],
                        best_score=quiz["best_score"],
                        study_topic_id=quiz.get("study_topic_id"),
                        difficulty=quiz.get("difficulty") or DEFAULT_QUIZ_DIFFICULTY,
                    )
                    for quiz in item["quizzes"]
                ],
            )
            for item in study_topics
        ],
        total_quizzes=total_quizzes,
        completed=completed,
        total_topics=sum(1 for item in study_topics if item["id"] is not None),
    )


@app.post(
    "/api/v1/study-topics/{study_topic_id}/practice",
    response_model=QuizResponse,
)
async def practice_study_topic(
    study_topic_id: int,
    request: PracticeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a new quiz on an existing study topic with different questions."""
    study_topic = get_study_topic_for_user(db, study_topic_id, current_user.id)
    if not study_topic:
        raise HTTPException(status_code=404, detail="Study topic not found")

    source_text = (study_topic.source_text or "").strip()
    if not source_text:
        label = study_topic.topic or study_topic.title
        if not label:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This study topic does not have enough material "
                    "to practice again."
                ),
            )
        source_text = f"Create a quiz about {label}."

    try:
        generated = as_generated_quiz(
            generate_quiz_from_text(
                source_text,
                study_topic.topic,
                request.num_questions,
                existing_questions=list_study_topic_questions(db, study_topic.id),
                difficulty=request.difficulty,
            ),
            study_topic.topic,
        )
        return _persist_generated_quiz(
            db,
            generated,
            current_user.id,
            study_topic_id=study_topic.id,
            requested_questions=request.num_questions,
            difficulty=request.difficulty,
        )
    except QuizGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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


@app.post(
    "/api/v1/quiz/{quiz_id}/questions/{question_id}/explain",
    response_model=ExplainResponse,
)
async def explain_question(
    quiz_id: int,
    question_id: int,
    request: ExplainRequest,
    db: Session = Depends(get_db),
):
    """Explain a quiz question using the study topic source when available."""
    try:
        explanation = generate_question_explanation(
            db,
            quiz_id,
            question_id,
            request.selected_answer,
        )
        return ExplainResponse(explanation=explanation)
    except QuizNotFoundError:
        raise HTTPException(status_code=404, detail="Quiz not found")
    except QuestionNotFoundError:
        raise HTTPException(status_code=404, detail="Question not found")
    except InvalidSelectionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ExplanationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


if __name__ == "__main__":
    import uvicorn

    # Binding to all interfaces is intentional for Docker deployment
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
