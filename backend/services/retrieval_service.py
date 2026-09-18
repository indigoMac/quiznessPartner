"""Embedding and similarity search over study topic source material.

Quiz generation samples a spread of chunks from the raw text, which is enough
to write questions but cannot answer "what does my material say about X".
This module indexes every chunk with an embedding so passages can be looked
up by meaning rather than position.

Embeddings come from a different provider than quiz generation: Groq serves
no embeddings endpoint, so this defaults to OpenAI and is configured
independently via the EMBEDDING_* environment variables.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Sequence

from openai import OpenAI
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_utils import split_text
from models.source_chunk import EMBEDDING_DIMENSIONS, SourceChunk

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_BASE_URL = "https://api.openai.com/v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# Smaller than the quiz generation chunks: retrieval wants passages precise
# enough that a match points at the relevant sentences, not a whole page.
RETRIEVAL_CHUNK_SIZE = 1000
RETRIEVAL_CHUNK_OVERLAP = 150
MAX_EMBEDDING_BATCH = 96


class RetrievalError(Exception):
    """Raised when indexing or searching fails and the caller should know."""


@dataclass
class RetrievedChunk:
    """A source passage and how closely it matched the query."""

    chunk_index: int
    content: str
    # Cosine distance: 0.0 is identical, 2.0 is opposite.
    distance: float


def retrieval_enabled() -> bool:
    """Indexing costs money per upload, so it is opt-in per environment."""
    return os.getenv("RETRIEVAL_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def _embedding_api_key() -> str:
    return os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY") or ""


def _embedding_base_url() -> str:
    return os.getenv("EMBEDDING_BASE_URL", DEFAULT_EMBEDDING_BASE_URL)


def _embedding_model() -> str:
    return os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def embed_texts(texts: Sequence[str]) -> List[List[float]]:
    """Embed texts in order, batching to stay within provider request limits."""
    if not texts:
        return []
    if not _embedding_api_key():
        raise RetrievalError("No embedding API key is configured.")

    client = OpenAI(api_key=_embedding_api_key(), base_url=_embedding_base_url())
    model = _embedding_model()
    vectors: List[List[float]] = []

    for start in range(0, len(texts), MAX_EMBEDDING_BATCH):
        batch = list(texts[start : start + MAX_EMBEDDING_BATCH])
        try:
            response = client.embeddings.create(model=model, input=batch)
        except Exception as exc:
            logger.exception("Embedding request failed")
            raise RetrievalError("Could not embed the source material.") from exc

        # The API may return items out of order, so sort by the index it gives.
        ordered = sorted(response.data, key=lambda item: item.index)
        for item in ordered:
            if len(item.embedding) != EMBEDDING_DIMENSIONS:
                raise RetrievalError(
                    f"Embedding model {model} returned "
                    f"{len(item.embedding)} dimensions, expected "
                    f"{EMBEDDING_DIMENSIONS}. Update EMBEDDING_DIMENSIONS and "
                    "re-index if the model changed."
                )
            vectors.append(list(item.embedding))

    return vectors


def chunk_source_text(text: str) -> List[str]:
    """Split source material into passages small enough to match precisely."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []
    return [
        chunk.strip()
        for chunk in split_text(
            cleaned,
            chunk_size=RETRIEVAL_CHUNK_SIZE,
            chunk_overlap=RETRIEVAL_CHUNK_OVERLAP,
        )
        if chunk.strip()
    ]


def index_study_topic(db: Session, study_topic_id: int, text: str) -> int:
    """Replace a study topic's indexed passages. Returns how many were stored.

    Re-indexing deletes first so a topic whose source changed does not keep
    stale passages alongside the new ones.
    """
    chunks = chunk_source_text(text)
    db.execute(delete(SourceChunk).where(SourceChunk.study_topic_id == study_topic_id))
    if not chunks:
        db.commit()
        return 0

    embeddings = embed_texts(chunks)
    db.add_all(
        [
            SourceChunk(
                study_topic_id=study_topic_id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
            )
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
    )
    db.commit()
    logger.info("Indexed %s passages for study topic %s", len(chunks), study_topic_id)
    return len(chunks)


def search_study_topic(
    db: Session,
    study_topic_id: int,
    query: str,
    limit: int = 5,
    max_distance: Optional[float] = None,
) -> List[RetrievedChunk]:
    """Find the passages of a study topic closest in meaning to the query.

    Requires PostgreSQL with pgvector; the cosine distance operator does not
    exist on SQLite.
    """
    if not query or not query.strip():
        return []

    embedding = embed_texts([query])[0]
    distance = SourceChunk.embedding.cosine_distance(embedding)
    statement = (
        select(SourceChunk, distance.label("distance"))
        .where(SourceChunk.study_topic_id == study_topic_id)
        .order_by(distance)
        .limit(limit)
    )
    if max_distance is not None:
        statement = statement.where(distance <= max_distance)

    return [
        RetrievedChunk(
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=float(value),
        )
        for chunk, value in db.execute(statement).all()
    ]
