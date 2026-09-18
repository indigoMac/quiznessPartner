from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from models.base import Base

# text-embedding-3-small returns 1536 dimensions. Changing the embedding model
# means changing this and re-indexing, because stored vectors of a different
# width cannot be compared against new ones.
EMBEDDING_DIMENSIONS = 1536


class SourceChunk(Base):
    """One embedded passage of a study topic's source material.

    Quiz generation samples a spread of chunks from the raw text. This table
    instead keeps every chunk with its embedding, so questions and answers can
    be grounded in the passage that is actually relevant to them.
    """

    __tablename__ = "source_chunks"

    id = Column(Integer, primary_key=True, index=True)
    study_topic_id = Column(
        Integer,
        ForeignKey("study_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # The test suite runs on SQLite, which has no vector type. Similarity
    # search needs PostgreSQL; on SQLite the column only round-trips a list.
    embedding = Column(
        Vector(EMBEDDING_DIMENSIONS).with_variant(JSON(), "sqlite"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    study_topic = relationship("StudyTopic", backref="source_chunks")
