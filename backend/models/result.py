from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from models.base import Base

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, nullable=False)
    answers = Column(JSON, nullable=False)  # List of user's answers
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="results")
    quiz = relationship("Quiz", backref="results") 