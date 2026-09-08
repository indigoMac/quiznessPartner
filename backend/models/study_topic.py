from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from models.base import Base


class StudyTopic(Base):
    """A study topic groups quizzes generated from the same material."""

    __tablename__ = "study_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    source_text = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="study_topics")
    quizzes = relationship("Quiz", back_populates="study_topic")
