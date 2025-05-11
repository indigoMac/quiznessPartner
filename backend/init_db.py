from db import engine
from models.base import Base
from models.user import User
from models.quiz import Quiz
from models.question import Question
from models.result import Result

def init_db():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 