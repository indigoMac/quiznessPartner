from db import get_engine
from models.base import Base
from models.question import Question  # noqa: F401
from models.quiz import Quiz  # noqa: F401
from models.result import Result  # noqa: F401
from models.study_topic import StudyTopic  # noqa: F401
from models.user import User  # noqa: F401


def init_db():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=get_engine())
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
