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


SOURCE_CHUNK_SIZE = 3500
MAX_SOURCE_CHUNKS = 4
MAX_QUESTIONS = 20


def select_source_chunks(
    text: str, chunk_size: int = SOURCE_CHUNK_SIZE, max_chunks: int = MAX_SOURCE_CHUNKS
) -> List[str]:
    """Split long sources and keep a spread of chunks, not just the opening."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks = [
        chunk.strip()
        for chunk in split_text(cleaned, chunk_size=chunk_size)
        if chunk.strip()
    ]
    if len(chunks) <= max_chunks:
        return chunks

    last_index = len(chunks) - 1
    indexes = [
        round(i * last_index / (max_chunks - 1)) for i in range(max_chunks)
    ]
    selected = []
    seen = set()
    for index in indexes:
        if index not in seen:
            selected.append(chunks[index])
            seen.add(index)
    return selected


def _question_counts(num_questions: int, chunk_count: int) -> List[int]:
    if chunk_count <= 0:
        return []
    base, remainder = divmod(num_questions, chunk_count)
    return [base + (1 if i < remainder else 0) for i in range(chunk_count)]


def _strip_json_fences(result: str) -> str:
    if result.startswith("```json"):
        result = result.replace("```json", "", 1)
    if result.endswith("```"):
        result = result.replace("```", "", 1)
    return result.strip()


def _normalize_question_text(question: str) -> str:
    return " ".join(str(question).lower().split())


def _dedupe_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    seen = set()
    for question in questions:
        key = _normalize_question_text(question.get("question", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(question)
    return unique


def _validate_questions(questions: Any) -> List[Dict[str, Any]]:
    if not isinstance(questions, list) or not questions:
        raise QuizGenerationError(
            "Quiz generation returned no questions. Try different content."
        )

    for question in questions:
        if (
            "question" not in question
            or "options" not in question
            or "correct_answer" not in question
        ):
            raise QuizGenerationError(
                "Quiz generation returned an invalid question. Please try again."
            )
        if not isinstance(question["options"], list) or len(question["options"]) < 2:
            raise QuizGenerationError(
                "Quiz generation returned invalid answer options. Please try again."
            )
        if not isinstance(question["correct_answer"], int):
            try:
                question["correct_answer"] = int(question["correct_answer"])
            except (TypeError, ValueError) as exc:
                raise QuizGenerationError(
                    "Quiz generation returned an invalid correct answer. "
                    "Please try again."
                ) from exc
    return questions


def _parse_quiz_payload(result: str) -> Dict[str, Any]:
    result = _strip_json_fences(result)
    try:
        payload = json.loads(result)
    except json.JSONDecodeError as exc:
        logger.error("Quiz generation returned invalid JSON: %s", result)
        raise QuizGenerationError(
            "Quiz generation returned invalid data. Please try again."
        ) from exc

    if isinstance(payload, list):
        return {"title": None, "topic": None, "questions": payload}
    if isinstance(payload, dict):
        return {
            "title": payload.get("title"),
            "topic": payload.get("topic"),
            "questions": payload.get("questions"),
        }
    raise QuizGenerationError(
        "Quiz generation returned invalid data. Please try again."
    )


def _build_quiz_prompt(
    text: str,
    topic: Optional[str],
    num_questions: int,
    include_metadata: bool,
    existing_questions: Optional[List[Dict[str, Any]]] = None,
) -> str:
    topic_str = (
        f"on the topic of {topic}" if topic else "based on the following content"
    )
    avoid = ""
    if existing_questions:
        listed = "; ".join(
            item.get("question", "") for item in existing_questions[:12]
        )
        avoid = f"\nDo not repeat these questions: {listed}\n"

    if include_metadata:
        return f"""
    Create a multiple-choice quiz {topic_str}.
    Generate {num_questions} challenging but fair questions.
    {avoid}
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

    return f"""
    Create {num_questions} multiple-choice questions {topic_str}.
    {avoid}
    Text: {text}

    Format your response as a valid JSON array with objects containing:
    1. 'question': The question text
    2. 'options': An array of 4 possible answers (as strings)
    3. 'correct_answer': The index (0-3) of the correct answer

    ONLY return the JSON array, nothing else.
    """


def _generate_from_chunk(
    text: str,
    topic: Optional[str],
    num_questions: int,
    include_metadata: bool,
    existing_questions: Optional[List[Dict[str, Any]]] = None,
) -> GeneratedQuiz:
    prompt = _build_quiz_prompt(
        text, topic, num_questions, include_metadata, existing_questions
    )
    try:
        result = _chat_completion(prompt)
    except QuizGenerationError:
        raise
    except Exception as exc:
        logger.exception("Quiz generation failed")
        raise QuizGenerationError(
            "Quiz generation failed. Please try again."
        ) from exc

    parsed = _parse_quiz_payload(result)
    questions = _validate_questions(parsed["questions"])
    return GeneratedQuiz(
        title=resolve_quiz_title(parsed["title"], topic, questions),
        topic=_clean_label(topic, 60) or _clean_label(parsed["topic"], 60),
        questions=questions,
    )


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

    Long sources are split into several chunks so questions cover more than
    the opening paragraphs. Defaults to Groq (OpenAI-compatible).
    """
    if not text or not text.strip():
        raise QuizGenerationError("No text was provided to generate a quiz from.")

    num_questions = max(1, min(int(num_questions), MAX_QUESTIONS))
    chunks = select_source_chunks(text)
    if not chunks:
        raise QuizGenerationError("No text was provided to generate a quiz from.")

    counts = _question_counts(num_questions, len(chunks))
    collected: List[Dict[str, Any]] = []
    title: Optional[str] = None
    inferred_topic: Optional[str] = topic

    for index, (chunk, count) in enumerate(zip(chunks, counts)):
        if count <= 0:
            continue
        include_metadata = index == 0
        try:
            part = _generate_from_chunk(
                chunk,
                topic,
                count,
                include_metadata,
                existing_questions=collected,
            )
        except QuizGenerationError:
            if not collected:
                raise
            logger.warning("Skipping source chunk %s after generation failed", index)
            continue

        if include_metadata:
            title = part.title
            inferred_topic = part.topic
        collected.extend(part.questions)

    questions = _dedupe_questions(collected)[:num_questions]
    if not questions:
        raise QuizGenerationError(
            "Quiz generation returned no questions. Try different content."
        )

    return GeneratedQuiz(
        title=resolve_quiz_title(title, inferred_topic, questions),
        topic=_clean_label(inferred_topic, 60),
        questions=questions,
    )
