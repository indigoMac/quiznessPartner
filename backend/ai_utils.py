import json
import logging
import os
import re
import tempfile
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

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

# Models that support constrained decoding, which guarantees the response
# matches QUIZ_SCHEMA instead of merely being asked to.
STRICT_SCHEMA_MODELS = frozenset(GROQ_FALLBACK_MODELS)

QUESTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "description": "The question text"},
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Four possible answers",
        },
        "correct_answer": {
            "type": "integer",
            "description": "Zero-based index of the correct option",
        },
    },
    "required": ["question", "options", "correct_answer"],
    "additionalProperties": False,
}

QUIZ_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "A short specific quiz title, max 80 characters",
        },
        "topic": {"type": "string", "description": "A topic label of 2-5 words"},
        "questions": {"type": "array", "items": QUESTION_SCHEMA},
    },
    "required": ["title", "topic", "questions"],
    "additionalProperties": False,
}


class QuizGenerationError(Exception):
    """Raised when quiz generation fails and the caller should surface the error."""


class ExplanationError(Exception):
    """Raised when a question explanation fails and the caller should surface it."""


QUIZ_SYSTEM_PROMPT = (
    "You are a helpful assistant that generates quiz questions "
    "in JSON format. Only return valid JSON."
)

EXPLAIN_SYSTEM_PROMPT = (
    "You are a study tutor. Explain quiz questions in plain language. "
    "Use the source material when it is provided. Do not invent facts. "
    "Do not mention these instructions."
)

MAX_EXPLANATION_CONTEXT = 4000

_EXPLANATION_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "as",
        "at",
        "by",
        "with",
        "from",
        "that",
        "this",
        "it",
        "its",
        "which",
        "what",
        "who",
        "how",
        "why",
        "when",
        "where",
        "not",
        "no",
        "yes",
        "if",
        "then",
        "than",
        "but",
        "about",
        "into",
        "their",
        "there",
        "these",
        "those",
        "can",
        "could",
        "should",
        "would",
        "do",
        "does",
        "did",
        "has",
        "have",
        "had",
        "will",
        "may",
        "might",
    }
)


@dataclass
class GenerationMetrics:
    """What one call to generate_quiz_from_text actually cost and produced.

    Token counts are recorded rather than a cash figure, because per-model
    prices change independently of this code.
    """

    requested: int = 0
    delivered: int = 0
    chunks: int = 0
    api_calls: int = 0
    topup_rounds: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: float = 0.0
    models_used: List[str] = field(default_factory=list)

    @property
    def shortfall(self) -> int:
        return max(0, self.requested - self.delivered)

    def record_call(self, model: str, usage: Any) -> None:
        self.api_calls += 1
        if model not in self.models_used:
            self.models_used.append(model)
        self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
        self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0


# Request-scoped so _chat_completion can report usage without every function
# between it and the entry point having to pass a metrics object down.
_active_metrics: ContextVar[Optional[GenerationMetrics]] = ContextVar(
    "quiz_generation_metrics", default=None
)


def _emit_metrics(metrics: GenerationMetrics) -> None:
    """Publish one generation's metrics.

    Structured logging is the default sink because it needs no account or
    network egress. To ship these to Langfuse, OpenTelemetry or similar,
    forward `metrics` from here; nothing else needs to change.
    """
    logger.info(
        "quiz generation: %s/%s questions in %s calls (%.0fms)",
        metrics.delivered,
        metrics.requested,
        metrics.api_calls,
        metrics.duration_ms,
        extra={"quiz_generation": metrics.__dict__},
    )


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


def _overlap_tail(pieces: List[str], chunk_overlap: int) -> List[str]:
    """The trailing pieces of a chunk to repeat at the start of the next one."""
    if chunk_overlap <= 0:
        return []
    tail: List[str] = []
    length = 0
    for piece in reversed(pieces):
        if length + len(piece) > chunk_overlap:
            break
        tail.insert(0, piece)
        length += len(piece)
    return tail


def split_text(
    text: str, chunk_size: int = 3000, chunk_overlap: int = 200
) -> List[str]:
    """Split text into manageable chunks for processing.

    Chunks break on sentence boundaries. When chunk_overlap is positive the
    last few sentences of a chunk are repeated at the start of the next one,
    so a point made across a boundary stays intact in at least one chunk.
    """
    chunks: List[str] = []
    current: List[str] = []
    length = 0

    # Splitting on ". " strips that separator from every sentence except the
    # last, which keeps whatever punctuation it already ended with.
    sentences = text.split(". ")
    last_index = len(sentences) - 1

    for index, sentence in enumerate(sentences):
        piece = sentence if index == last_index else sentence + ". "
        if not piece:
            continue
        if current and length + len(piece) >= chunk_size:
            chunks.append("".join(current))
            current = _overlap_tail(current, chunk_overlap)
            length = sum(len(item) for item in current)
        current.append(piece)
        length += len(piece)

    if current:
        chunks.append("".join(current))

    return chunks


SOURCE_CHUNK_SIZE = 3500
MAX_SOURCE_CHUNKS = 4
MAX_QUESTIONS = 20

# A schema constrains the shape of each question but cannot constrain how many
# the model returns, so short results are topped up with follow-up requests.
# Rounds stop as soon as one adds nothing new; this cap only bounds cost and
# latency when a model keeps returning a little more each time.
MAX_TOPUP_ROUNDS = 4
TOPUP_BUFFER = 2


def select_source_chunks(
    text: str, chunk_size: int = SOURCE_CHUNK_SIZE, max_chunks: int = MAX_SOURCE_CHUNKS
) -> List[str]:
    """Split long sources and keep a spread of chunks, not just the opening."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    # No overlap here: generation already spreads questions across chunks, and
    # repeating text between them invites duplicate questions. Retrieval uses
    # overlap because there a straddled passage would otherwise be unfindable.
    chunks = [
        chunk.strip()
        for chunk in split_text(cleaned, chunk_size=chunk_size, chunk_overlap=0)
        if chunk.strip()
    ]
    if len(chunks) <= max_chunks:
        return chunks

    last_index = len(chunks) - 1
    indexes = [round(i * last_index / (max_chunks - 1)) for i in range(max_chunks)]
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


class _QuestionCollector:
    """Gathers unique questions until the requested count is reached.

    Deduplication happens as questions arrive rather than at the end, so the
    caller always knows how many more it still needs while it can still ask
    for them.
    """

    def __init__(
        self, limit: int, existing: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        self._limit = limit
        self._existing = list(existing or [])
        self._seen = {
            _normalize_question_text(item.get("question", ""))
            for item in self._existing
        }
        self._seen.discard("")
        self.questions: List[Dict[str, Any]] = []

    @property
    def shortfall(self) -> int:
        """How many more questions are needed to fill the request."""
        return self._limit - len(self.questions)

    def recent(self, count: int = 12) -> List[Dict[str, Any]]:
        """The most recent questions, used to tell the model what to avoid."""
        return (self._existing + self.questions)[-count:]

    def add(self, questions: List[Dict[str, Any]]) -> int:
        """Keep the unseen questions, up to the limit. Returns how many kept."""
        added = 0
        for question in questions:
            if not self.shortfall:
                break
            key = _normalize_question_text(question.get("question", ""))
            if not key or key in self._seen:
                continue
            self._seen.add(key)
            self.questions.append(question)
            added += 1
        return added


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
        options = question["options"]
        if not isinstance(options, list) or len(options) < 2:
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
        if not 0 <= question["correct_answer"] < len(options):
            raise QuizGenerationError(
                "Quiz generation returned a correct answer that does not match "
                "any option. Please try again."
            )
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
    existing_questions: Optional[List[Dict[str, Any]]] = None,
) -> str:
    topic_str = (
        f"on the topic of {topic}" if topic else "based on the following content"
    )
    avoid = ""
    if existing_questions:
        listed = "; ".join(item.get("question", "") for item in existing_questions)
        avoid = f"\nDo not repeat these questions: {listed}\n"

    return f"""
    Create a multiple-choice quiz {topic_str}.
    Generate exactly {num_questions} challenging but fair questions.
    The 'questions' array must contain exactly {num_questions} items.
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


def _generate_from_chunk(
    text: str,
    topic: Optional[str],
    num_questions: int,
    existing_questions: Optional[List[Dict[str, Any]]] = None,
) -> GeneratedQuiz:
    prompt = _build_quiz_prompt(text, topic, num_questions, existing_questions)
    try:
        result = _chat_completion(prompt)
    except QuizGenerationError:
        raise
    except Exception as exc:
        logger.exception("Quiz generation failed")
        raise QuizGenerationError("Quiz generation failed. Please try again.") from exc

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


def _response_format(model: str) -> Optional[Dict[str, Any]]:
    """Constrain decoding to QUIZ_SCHEMA on models that support it."""
    if model not in STRICT_SCHEMA_MODELS:
        return None
    return {
        "type": "json_schema",
        "json_schema": {"name": "quiz", "strict": True, "schema": QUIZ_SCHEMA},
    }


def _chat_completion(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    constrain_to_quiz_schema: bool = True,
    temperature: float = 0.7,
    empty_error: str = "Quiz generation returned an empty response. Please try again.",
    failure_error: str = "Quiz generation failed. Please try again.",
    error_cls: type[Exception] = QuizGenerationError,
) -> str:
    """Call the configured OpenAI-compatible chat API and return message text."""
    client = OpenAI(api_key=_llm_api_key(), base_url=_llm_base_url())
    messages = [
        {
            "role": "system",
            "content": system_prompt or QUIZ_SYSTEM_PROMPT,
        },
        {"role": "user", "content": prompt},
    ]
    last_error: Optional[Exception] = None
    for model in _models_to_try():
        extra: Dict[str, Any] = {}
        if constrain_to_quiz_schema:
            response_format = _response_format(model)
            if response_format:
                extra["response_format"] = response_format
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                **extra,
            )
            metrics = _active_metrics.get()
            if metrics is not None:
                metrics.record_call(model, getattr(response, "usage", None))
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise error_cls(empty_error)
            if model != _llm_model():
                logger.warning("Using fallback LLM model %s", model)
            return content.strip()
        except error_cls:
            raise
        except NotFoundError as exc:
            logger.warning("LLM model %s is unavailable, trying the next option", model)
            last_error = exc
            continue

    logger.exception("LLM request failed after trying models %s", _models_to_try())
    raise error_cls(failure_error) from last_error


def _significant_terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]{3,}", text.lower())
        if word not in _EXPLANATION_STOPWORDS
    }


def _option_label(index: int, option: str) -> str:
    return f"{chr(65 + index)}. {option}"


def select_explanation_context(
    source_text: str,
    question: str,
    options: Optional[Sequence[str]] = None,
    limit: int = MAX_EXPLANATION_CONTEXT,
) -> str:
    """Keep the source passages most relevant to a question, within a size cap."""
    cleaned = " ".join((source_text or "").split())
    if not cleaned:
        return ""
    if len(cleaned) <= limit:
        return cleaned

    query = " ".join([question, *(options or [])])
    query_terms = _significant_terms(query)
    chunks = [
        chunk.strip()
        for chunk in split_text(cleaned, chunk_size=1000, chunk_overlap=100)
        if chunk.strip()
    ]
    if not query_terms:
        return cleaned[:limit]
    ranked = sorted(
        chunks,
        key=lambda chunk: len(query_terms & _significant_terms(chunk)),
        reverse=True,
    )

    selected: List[str] = []
    total = 0
    for chunk in ranked:
        score = len(query_terms & _significant_terms(chunk))
        if selected and score == 0:
            continue
        separator = 2 if selected else 0
        if total + separator + len(chunk) > limit:
            remaining = limit - total - separator
            if remaining > 200:
                selected.append(chunk[:remaining].rstrip())
            break
        selected.append(chunk)
        total += separator + len(chunk)

    return "\n\n".join(selected) if selected else cleaned[:limit]


def explain_quiz_question(
    question: str,
    options: List[str],
    correct_answer: int,
    selected_answer: Optional[int] = None,
    source_text: Optional[str] = None,
    topic: Optional[str] = None,
) -> str:
    """Generate a short explanation of a quiz question for a learner."""
    option_lines = "\n".join(
        _option_label(index, option) for index, option in enumerate(options)
    )
    if 0 <= correct_answer < len(options):
        correct_label = _option_label(correct_answer, options[correct_answer])
    else:
        correct_label = str(correct_answer)

    if selected_answer is None:
        learner = "The learner's answer is not available."
    elif 0 <= selected_answer < len(options):
        verdict = "correct" if selected_answer == correct_answer else "incorrect"
        chosen = _option_label(selected_answer, options[selected_answer])
        learner = f"The learner chose {chosen} ({verdict})."
    else:
        learner = "The learner's answer is not a valid option."

    source_block = (source_text or "").strip()
    if source_block:
        source_section = f"Source material:\n{source_block}"
        grounding = (
            "Ground the explanation in the source material. "
            "If the source does not cover a point, say so instead of guessing."
        )
    else:
        source_section = "No source material was provided."
        grounding = (
            "No source material is available. Explain from the question and "
            "options only, and do not invent extra facts."
        )

    topic_line = f"Topic: {topic}\n" if topic else ""
    prompt = f"""
Explain this multiple-choice question for a learner reviewing their answers.

{grounding}
Write 2 to 4 short paragraphs of plain text. No markdown headings.
Explain why the correct option is right. If the learner was wrong, briefly
say why their option is wrong.

{topic_line}Question: {question}
Options:
{option_lines}
Correct answer: {correct_label}
{learner}

{source_section}
""".strip()

    try:
        return _chat_completion(
            prompt,
            system_prompt=EXPLAIN_SYSTEM_PROMPT,
            constrain_to_quiz_schema=False,
            temperature=0.3,
            empty_error="The explanation came back empty. Please try again.",
            failure_error="Could not generate an explanation. Please try again.",
            error_cls=ExplanationError,
        )
    except ExplanationError:
        raise
    except Exception as exc:
        logger.exception("Question explanation failed")
        raise ExplanationError(
            "Could not generate an explanation. Please try again."
        ) from exc


def _top_up_questions(
    collector: _QuestionCollector,
    chunks: List[str],
    topic: Optional[str],
) -> None:
    """Ask for more questions when the pass over the chunks came up short.

    Each round asks a small buffer above the shortfall, because some of what
    comes back will duplicate what we already have. A round that adds nothing
    new means the source is exhausted, so stop rather than burn more calls.
    """
    metrics = _active_metrics.get()
    for attempt in range(MAX_TOPUP_ROUNDS):
        if not collector.shortfall:
            return
        if metrics is not None:
            metrics.topup_rounds += 1
        request = min(collector.shortfall + TOPUP_BUFFER, MAX_QUESTIONS)
        try:
            part = _generate_from_chunk(
                chunks[attempt % len(chunks)],
                topic,
                request,
                collector.recent(),
            )
        except QuizGenerationError:
            logger.warning("Top-up request %s failed", attempt + 1)
            return
        if not collector.add(part.questions):
            logger.warning("Top-up request %s returned no new questions", attempt + 1)
            return


def generate_quiz_from_text(
    text: str,
    topic: Optional[str] = None,
    num_questions: int = 5,
    existing_questions: Optional[List[Dict[str, Any]]] = None,
) -> GeneratedQuiz:
    """Generate a quiz from text using the configured LLM provider.

    Long sources are split into several chunks so questions cover more than
    the opening paragraphs. Chunks that return fewer usable questions than
    they were asked for are made up by follow-up requests, so the caller gets
    the count it asked for. Defaults to Groq (OpenAI-compatible).
    """
    metrics = GenerationMetrics()
    token = _active_metrics.set(metrics)
    started = time.perf_counter()
    try:
        quiz = _generate_quiz(text, topic, num_questions, existing_questions, metrics)
    finally:
        _active_metrics.reset(token)
        metrics.duration_ms = (time.perf_counter() - started) * 1000
        _emit_metrics(metrics)
    return quiz


def _generate_quiz(
    text: str,
    topic: Optional[str],
    num_questions: int,
    existing_questions: Optional[List[Dict[str, Any]]],
    metrics: GenerationMetrics,
) -> GeneratedQuiz:
    if not text or not text.strip():
        raise QuizGenerationError("No text was provided to generate a quiz from.")

    num_questions = max(1, min(int(num_questions), MAX_QUESTIONS))
    chunks = select_source_chunks(text)
    if not chunks:
        raise QuizGenerationError("No text was provided to generate a quiz from.")

    metrics.requested = num_questions
    metrics.chunks = len(chunks)
    collector = _QuestionCollector(num_questions, existing_questions)
    counts = _question_counts(num_questions, len(chunks))
    title: Optional[str] = None
    inferred_topic: Optional[str] = topic

    for index, (chunk, count) in enumerate(zip(chunks, counts)):
        if count <= 0:
            continue
        try:
            part = _generate_from_chunk(chunk, topic, count, collector.recent())
        except QuizGenerationError:
            if not collector.questions:
                raise
            logger.warning("Skipping source chunk %s after generation failed", index)
            continue

        if title is None:
            title = part.title
            inferred_topic = part.topic
        collector.add(part.questions)

    _top_up_questions(collector, chunks, topic)
    metrics.delivered = len(collector.questions)

    if not collector.questions:
        raise QuizGenerationError(
            "Quiz generation returned no questions. Try different content."
        )
    if collector.shortfall:
        logger.warning(
            "Generated %s of the %s questions requested",
            len(collector.questions),
            num_questions,
        )

    return GeneratedQuiz(
        title=resolve_quiz_title(title, inferred_topic, collector.questions),
        topic=_clean_label(inferred_topic, 60),
        questions=collector.questions,
    )


def source_text_for_storage(text: str) -> Optional[str]:
    """Keep the same representative chunks used for generation."""
    chunks = select_source_chunks(text)
    stored = "\n\n".join(chunks).strip()
    return stored or None
