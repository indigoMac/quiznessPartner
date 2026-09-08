import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_LLM_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_LLM_MODEL = "llama-3.1-8b-instant"


class QuizGenerationError(Exception):
    """Raised when quiz generation fails and the caller should surface the error."""


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
    return os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_LLM_MODEL


def _chat_completion(prompt: str) -> str:
    """Call the configured OpenAI-compatible chat API and return message text."""
    client = OpenAI(api_key=_llm_api_key(), base_url=_llm_base_url())
    response = client.chat.completions.create(
        model=_llm_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that generates quiz questions "
                    "in JSON format. Only return valid JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise QuizGenerationError(
            "Quiz generation returned an empty response. Please try again."
        )
    return content.strip()


def generate_quiz_from_text(
    text: str, topic: Optional[str] = None, num_questions: int = 5
) -> List[Dict[str, Any]]:
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

    Format your response as a valid JSON array with objects containing:
    1. 'question': The question text
    2. 'options': An array of 4 possible answers (as strings)
    3. 'correct_answer': The index (0-3) of the correct answer in the options array

    ONLY return the JSON array, nothing else.
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
        questions = json.loads(result)
    except json.JSONDecodeError as exc:
        logger.error("Quiz generation returned invalid JSON: %s", result)
        raise QuizGenerationError(
            "Quiz generation returned invalid data. Please try again."
        ) from exc

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

    return questions
