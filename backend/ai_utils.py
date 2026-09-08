import json
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
from openai import NotFoundError, OpenAI

logger = logging.getLogger(__name__)

DEFAULT_LLM_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_LLM_MODEL = "openai/gpt-oss-20b"
DEPRECATED_LLM_MODELS = {
    "llama-3.1-8b-instant": "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
    "llama3-8b-8192": "openai/gpt-oss-20b",
    "llama3-70b-8192": "openai/gpt-oss-120b",
}
GROQ_FALLBACK_MODELS = ("openai/gpt-oss-20b", "openai/gpt-oss-120b")


class QuizGenerationError(Exception):
    """Raised when quiz generation fails and the caller should surface the error."""


@dataclass
class GeneratedQuiz:
    title: str
    topic: Optional[str]
    questions: List[Dict[str, Any]]


def _clean_label(value: Optional[str], max_len: int) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned[:max_len] if cleaned else None


def _title_from_questions(questions: List[Dict[str, Any]]) -> Optional[str]:
    first = questions[0].get("question") if questions else None
    if not isinstance(first, str) or not first.strip():
        return None
    snippet = " ".join(first.strip().rstrip("?").split()[:8]).strip()
    return snippet or None


def resolve_quiz_title(
    generated_title: Optional[str],
    topic: Optional[str],
    questions: List[Dict[str, Any]],
) -> str:
    title = _clean_label(generated_title, 80)
    if title:
        return title
    topic_label = _clean_label(topic, 60)
    if topic_label:
        return f"Quiz on {topic_label}"
    snippet = _title_from_questions(questions)
    if snippet:
        return snippet
    return "Untitled Quiz"


def as_generated_quiz(
    result: Any, requested_topic: Optional[str] = None
) -> GeneratedQuiz:
    """Normalize LLM output or test mocks into a GeneratedQuiz."""
    if isinstance(result, GeneratedQuiz):
        return result
    if isinstance(result, list):
        return GeneratedQuiz(
            title=resolve_quiz_title(None, requested_topic, result),
            topic=_clean_label(requested_topic, 60),
            questions=result,
        )
    raise QuizGenerationError(
        "Quiz generation returned invalid data. Please try again."
    )


def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(pdf_file.read())
        temp_file_path = temp_file.name

    try:
        doc = fitz.open(temp_file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    finally:
        os.unlink(temp_file_path)


def split_text(
    text: str, chunk_size: int = 3000, chunk_overlap: int = 200
) -> List[str]:
    """Split text into manageable chunks for processing."""
    chunks = []
    current_chunk = ""
    sentences = text.split(". ")

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _llm_api_key() -> str:
    return (
        os.getenv("LLM_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )


def _llm_base_url() -> str:
    return os.getenv("LLM_BASE_URL", DEFAULT_LLM_BASE_URL)


def _llm_model() -> str:
    requested = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_LLM_MODEL
    return DEPRECATED_LLM_MODELS.get(requested, requested)


def _models_to_try() -> List[str]:
    models = [_llm_model()]
    for fallback in GROQ_FALLBACK_MODELS:
        if fallback not in models:
            models.append(fallback)
    return models


def _chat_completion(prompt: str) -> str:
    """Call the configured OpenAI-compatible chat API and return message text."""
    client = OpenAI(api_key=_llm_api_key(), base_url=_llm_base_url())
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that generates quiz questions "
                "in JSON format. Only return valid JSON."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    last_error: Optional[Exception] = None
    for model in _models_to_try():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise QuizGenerationError(
                    "Quiz generation returned an empty response. Please try again."
                )
            if model != _llm_model():
                logger.warning("Using fallback LLM model %s", model)
            return content.strip()
        except QuizGenerationError:
            raise
        except NotFoundError as exc:
            logger.warning("LLM model %s is unavailable, trying the next option", model)
            last_error = exc
            continue

    logger.exception("Quiz generation failed after trying models %s", _models_to_try())
    raise QuizGenerationError(
        "Quiz generation failed. Please try again."
    ) from last_error


def generate_quiz_from_text(
    text: str, topic: Optional[str] = None, num_questions: int = 5
) -> GeneratedQuiz:
    """Generate a quiz from text using the configured LLM provider.

    Defaults to Groq (OpenAI-compatible). Override with LLM_BASE_URL,
    LLM_MODEL, and LLM_API_KEY / GROQ_API_KEY / OPENAI_API_KEY.
    """
    if not text or not text.strip():
        raise QuizGenerationError("No text was provided to generate a quiz from.")

    if len(text) > 4000:
        chunks = split_text(text)
        text = chunks[0]

    topic_str = (
        f"on the topic of {topic}" if topic else "based on the following content"
    )

    prompt = f"""
    Create a multiple-choice quiz {topic_str}.
    Generate {num_questions} challenging but fair questions.

    Text: {text}

    Format your response as a valid JSON object with:
    1. 'title': a short specific quiz title (max 80 characters)
    2. 'topic': a short topic label of 2-5 words
    3. 'questions': an array of objects containing:
       - 'question': The question text
       - 'options': An array of 4 possible answers (as strings)
       - 'correct_answer': The index (0-3) of the correct answer

    ONLY return the JSON object, nothing else.
    """

    try:
        result = _chat_completion(prompt)
    except QuizGenerationError:
        raise
    except Exception as exc:
        logger.exception("Quiz generation failed")
        raise QuizGenerationError(
            "Quiz generation failed. Please try again."
        ) from exc

    if result.startswith("```json"):
        result = result.replace("```json", "", 1)
    if result.endswith("```"):
        result = result.replace("```", "", 1)
    result = result.strip()

    try:
        payload = json.loads(result)
    except json.JSONDecodeError as exc:
        logger.error("Quiz generation returned invalid JSON: %s", result)
        raise QuizGenerationError(
            "Quiz generation returned invalid data. Please try again."
        ) from exc

    generated_title = None
    generated_topic = topic
    if isinstance(payload, list):
        questions = payload
    elif isinstance(payload, dict):
        questions = payload.get("questions")
        generated_title = payload.get("title")
        generated_topic = payload.get("topic") or topic
    else:
        raise QuizGenerationError(
            "Quiz generation returned invalid data. Please try again."
        )

    if not isinstance(questions, list) or not questions:
        raise QuizGenerationError(
            "Quiz generation returned no questions. Try different content."
        )

    for q in questions:
        if "question" not in q or "options" not in q or "correct_answer" not in q:
            raise QuizGenerationError(
                "Quiz generation returned an invalid question. Please try again."
            )
        if not isinstance(q["options"], list) or len(q["options"]) < 2:
            raise QuizGenerationError(
                "Quiz generation returned invalid answer options. Please try again."
            )
        if not isinstance(q["correct_answer"], int):
            try:
                q["correct_answer"] = int(q["correct_answer"])
            except (TypeError, ValueError) as exc:
                raise QuizGenerationError(
                    "Quiz generation returned an invalid correct answer. "
                    "Please try again."
                ) from exc

    return GeneratedQuiz(
        title=resolve_quiz_title(generated_title, topic, questions),
        topic=_clean_label(topic, 60) or _clean_label(generated_topic, 60),
        questions=questions,
    )
