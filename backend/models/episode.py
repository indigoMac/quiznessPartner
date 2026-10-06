from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import backref, relationship

from models.base import Base

EPISODE_PENDING = "pending"
EPISODE_READY = "ready"
EPISODE_FAILED = "failed"

# Version 1 has one episode per study topic. Regenerating replaces that row.
# script is a list of {chapter, speaker, text}. speaker is host_a or host_b.
# Stage 3 reads this shape for text-to-speech, so keep the keys stable.


class Episode(Base):
    """A two-speaker lesson generated from one study topic."""

    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint("study_topic_id", name="uq_episodes_study_topic_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    study_topic_id = Column(
        Integer,
        ForeignKey("study_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default=EPISODE_PENDING)
    title = Column(String, nullable=True)
    # Tests run on SQLite. JSON is the portable type this repo already uses
    # for question options and quiz answers.
    script = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    study_topic = relationship(
        "StudyTopic",
        backref=backref("episode", uselist=False, cascade="all, delete-orphan"),
    )
