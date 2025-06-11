from db import engine
from models.base import Base
# Import models to register them with SQLAlchemy metadata
from models.question import Question  # noqa: F401
from models.quiz import Quiz  # noqa: F401
from models.result import Result  # noqa: F401
from models.user import User  # noqa: F401


def init_db():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
