import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import openai

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY", "")


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


def generate_quiz_from_text(
    text: str, topic: Optional[str] = None, num_questions: int = 5
) -> List[Dict[str, Any]]:
    """Generate a quiz from text using OpenAI.

    Raises QuizGenerationError when generation fails so callers can show
    the failure instead of substituting dummy questions.
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
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
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
        result = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("OpenAI quiz generation failed")
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
